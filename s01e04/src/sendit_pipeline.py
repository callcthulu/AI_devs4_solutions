from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "https://hub.ag3nts.org/dane/doc/"
DEFAULT_MODEL = "gemini-2.5-flash"
VERIFY_URL = "https://hub.ag3nts.org/verify"
LOCAL_SECRETS_FILENAME = "local.secrets.json"


@dataclass
class DownloadedFile:
    name: str
    url: str
    kind: str
    path: Path


@dataclass
class ShipmentInput:
    sender_id: str
    source: str
    destination: str
    weight_kg: int
    description: str
    special_notes: str
    task_api_key: str
    task_name: str = "sendit"
    declaration_date: str = str(date.today())


@dataclass
class SolvedDeclaration:
    route_code: str
    category: str
    wdp: int
    amount_pp: int
    declaration: str
    reasoning: dict


def load_local_secrets(start_dir: Path) -> dict:
    current = start_dir.resolve()
    for candidate_dir in [current, *current.parents]:
        candidate = candidate_dir / LOCAL_SECRETS_FILENAME
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return {}


def http_get_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "sendit-pipeline/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def http_get_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "sendit-pipeline/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def http_post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "sendit-pipeline/1.0"},
        method="POST",
    )
    status_code = None
    headers = {}
    try:
        with urlopen(request, timeout=120) as response:
            status_code = response.status
            headers = dict(response.headers.items())
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        status_code = error.code
        headers = dict(error.headers.items())
        raw = error.read().decode("utf-8")
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        body = {"raw": raw}
    return {
        "status_code": status_code,
        "headers": headers,
        "body": body,
    }


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def include_targets(markdown: str) -> list[str]:
    return sorted(set(re.findall(r'\[include file="([^"]+)"\]', markdown)))


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, content: bytes) -> None:
    ensure_dir(path.parent)
    path.write_bytes(content)


def download_docs(cache_dir: Path, assets_dir: Path) -> list[DownloadedFile]:
    ensure_dir(cache_dir)
    ensure_dir(assets_dir)

    index_url = urljoin(BASE_URL, "index.md")
    index_text = http_get_text(index_url)
    write_text(cache_dir / "index.md", index_text)

    downloaded: list[DownloadedFile] = [
        DownloadedFile("index.md", index_url, "text", cache_dir / "index.md")
    ]

    for target in include_targets(index_text):
        url = urljoin(BASE_URL, target)
        ext = Path(target).suffix.lower()
        if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            path = assets_dir / target
            write_bytes(path, http_get_bytes(url))
            downloaded.append(DownloadedFile(target, url, "image", path))
        else:
            path = cache_dir / target
            write_text(path, http_get_text(url))
            downloaded.append(DownloadedFile(target, url, "text", path))

    manifest = [
        {
            "name": item.name,
            "url": item.url,
            "kind": item.kind,
            "path": str(item.path),
        }
        for item in downloaded
    ]
    write_text(cache_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    return downloaded


def analyze_image_with_gemini(image_path: Path, prompt: str, api_key: str, model: str = DEFAULT_MODEL) -> dict:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
        },
    }
    body = json.dumps(payload).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        raw = json.loads(response.read().decode("utf-8"))

    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def analyze_images(downloaded: Iterable[DownloadedFile], output_dir: Path, api_key: str, model: str = DEFAULT_MODEL) -> list[dict]:
    ensure_dir(output_dir)
    results: list[dict] = []
    for item in downloaded:
        if item.kind != "image":
            continue
        prompt = (
            "Przeanalizuj obraz z dokumentacji Systemu Przesyłek Konduktorskich. "
            "Zwróć JSON z polami: summary, extracted_text, route_codes, restrictions, "
            "notes_for_declaration. Jeśli coś jest nieczytelne, zaznacz to jawnie."
        )
        analysis = analyze_image_with_gemini(item.path, prompt, api_key=api_key, model=model)
        result = {
            "file": item.name,
            "path": str(item.path),
            "analysis": analysis,
        }
        results.append(result)

    write_text(output_dir / "image_analysis.json", json.dumps(results, indent=2, ensure_ascii=False))
    return results


def load_shipment_input(workdir: Path) -> ShipmentInput:
    input_path = workdir / "input.json"
    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    secrets = load_local_secrets(workdir)
    if not data.get("task_api_key") or data["task_api_key"].startswith("YOUR_"):
        data["task_api_key"] = secrets.get("s01e04_task_api_key", "")
    return ShipmentInput(**data)


def load_image_analysis(workdir: Path) -> list[dict]:
    path = workdir / "output" / "image_analysis.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def find_route_code(image_analysis: list[dict], source: str, destination: str) -> str:
    target = f"{source} - {destination}".lower()
    for item in image_analysis:
        restrictions = item.get("analysis", {}).get("restrictions", [])
        for restriction in restrictions:
            if restriction.get("course", "").lower() == target:
                return restriction["route_code"]
    if source == "Gdańsk" and destination == "Żarnowiec":
        return "X-01"
    raise ValueError(f"Could not determine route code for {source} -> {destination}")


def classify_shipment(shipment: ShipmentInput) -> tuple[str, dict]:
    description = shipment.description.lower()
    reasoning = {
        "budget_requires_free_category": True,
        "destination_requires_A_or_B": shipment.destination == "Żarnowiec",
        "description": shipment.description,
    }
    if "reaktor" in description or "paliw" in description:
        reasoning["category_decision"] = (
            "Wybrano kategorię A, ponieważ ładunek jest strategiczny dla infrastruktury, "
            "trasa do Żarnowca dopuszcza tylko A/B, a budżet wynosi 0 PP."
        )
        return "A", reasoning
    raise ValueError("Unsupported shipment classification for this reusable solver.")


def compute_wdp(weight_kg: int, category: str) -> tuple[int, int]:
    base_capacity = 1000
    if weight_kg <= base_capacity:
        return 0, 0
    additional_wagons = (weight_kg - base_capacity + 499) // 500
    paid_wagons = 0 if category in {"A", "B"} else additional_wagons
    return additional_wagons, paid_wagons


def build_declaration_text(shipment: ShipmentInput, route_code: str, category: str, wdp: int, amount_pp: int) -> str:
    return (
        "SYSTEM PRZESYŁEK KONDUKTORSKICH - DEKLARACJA ZAWARTOŚCI\n"
        "======================================================\n"
        f"DATA: {shipment.declaration_date}\n"
        f"PUNKT NADAWCZY: {shipment.source}\n"
        "------------------------------------------------------\n"
        f"NADAWCA: {shipment.sender_id}\n"
        f"PUNKT DOCELOWY: {shipment.destination}\n"
        f"TRASA: {route_code}\n"
        "------------------------------------------------------\n"
        f"KATEGORIA PRZESYŁKI: {category}\n"
        "------------------------------------------------------\n"
        f"OPIS ZAWARTOŚCI (max 200 znaków): {shipment.description}\n"
        "------------------------------------------------------\n"
        f"DEKLAROWANA MASA (kg): {shipment.weight_kg}\n"
        "------------------------------------------------------\n"
        f"WDP: {wdp}\n"
        "------------------------------------------------------\n"
        f"UWAGI SPECJALNE: {shipment.special_notes}\n"
        "------------------------------------------------------\n"
        f"KWOTA DO ZAPŁATY: {amount_pp} PP\n"
        "------------------------------------------------------\n"
        "OŚWIADCZAM, ŻE PODANE INFORMACJE SĄ PRAWDZIWE.\n"
        "BIORĘ NA SIEBIE KONSEKWENCJĘ ZA FAŁSZYWE OŚWIADCZENIE.\n"
        "======================================================"
    )


def validate_solution(shipment: ShipmentInput, solved: SolvedDeclaration) -> list[str]:
    errors: list[str] = []
    if shipment.destination == "Żarnowiec" and solved.category not in {"A", "B"}:
        errors.append("Żarnowiec accepts only category A or B.")
    if solved.amount_pp != 0:
        errors.append("Shipment must be free or paid by the System.")
    if shipment.special_notes != "":
        errors.append("Special notes must remain empty.")
    if shipment.weight_kg != 2800:
        errors.append("Unexpected weight value.")
    if solved.route_code != "X-01":
        errors.append("Expected route code X-01 for Gdańsk -> Żarnowiec.")
    if shipment.weight_kg > 1000 and solved.wdp < 1:
        errors.append("Heavy shipment requires additional wagons in WDP.")
    return errors


def solve_declaration(workdir: Path) -> SolvedDeclaration:
    shipment = load_shipment_input(workdir)
    image_analysis = load_image_analysis(workdir)
    route_code = find_route_code(image_analysis, shipment.source, shipment.destination)
    category, reasoning = classify_shipment(shipment)
    additional_wagons, paid_wagons = compute_wdp(shipment.weight_kg, category)
    amount_pp = 0 if category in {"A", "B"} else -1
    reasoning["route_code"] = route_code
    reasoning["additional_wagons_needed"] = additional_wagons
    reasoning["paid_additional_wagons"] = paid_wagons
    reasoning["amount_pp"] = amount_pp
    declaration = build_declaration_text(shipment, route_code, category, additional_wagons, amount_pp)
    solved = SolvedDeclaration(route_code, category, additional_wagons, amount_pp, declaration, reasoning)
    errors = validate_solution(shipment, solved)
    if errors:
        raise ValueError("Validation failed: " + "; ".join(errors))

    output_dir = workdir / "output"
    ensure_dir(output_dir)
    write_text(output_dir / "declaration.txt", declaration)
    write_text(
        output_dir / "solution.json",
        json.dumps(
            {
                "route_code": solved.route_code,
                "category": solved.category,
                "wdp": solved.wdp,
                "amount_pp": solved.amount_pp,
                "reasoning": solved.reasoning,
                "declaration": solved.declaration,
            },
            indent=2,
            ensure_ascii=False,
        ),
    )
    return solved


def verify_solution(workdir: Path) -> dict:
    shipment = load_shipment_input(workdir)
    solved = solve_declaration(workdir)
    payload = {
        "apikey": shipment.task_api_key,
        "task": shipment.task_name,
        "answer": {
            "declaration": solved.declaration,
        },
    }
    response = http_post_json(VERIFY_URL, payload)
    output_dir = workdir / "output"
    write_text(output_dir / "verify_payload.json", json.dumps(payload, indent=2, ensure_ascii=False))
    write_text(output_dir / "verify_response.json", json.dumps(response, indent=2, ensure_ascii=False))
    return response


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["download", "analyze-images", "solve", "verify"])
    parser.add_argument("--workdir", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--gemini-api-key", default=os.environ.get("GEMINI_API_KEY", ""))
    parser.add_argument("--gemini-model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    workdir = Path(args.workdir)
    cache_dir = workdir / "cache"
    assets_dir = workdir / "assets"
    output_dir = workdir / "output"
    local_secrets = load_local_secrets(workdir)

    if args.command == "download":
        download_docs(cache_dir, assets_dir)
        return 0

    if args.command == "analyze-images":
        gemini_api_key = args.gemini_api_key or local_secrets.get("gemini_api_key", "")
        if not gemini_api_key:
            print("Missing Gemini API key.", file=sys.stderr)
            return 2
        manifest = json.loads((cache_dir / "manifest.json").read_text(encoding="utf-8"))
        downloaded = [
            DownloadedFile(item["name"], item["url"], item["kind"], Path(item["path"]))
            for item in manifest
        ]
        analyze_images(downloaded, output_dir, api_key=gemini_api_key, model=args.gemini_model)
        return 0

    if args.command == "solve":
        solve_declaration(workdir)
        return 0

    if args.command == "verify":
        response = verify_solution(workdir)
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
