# s01e04 - sendit

To rozwiązanie jest przygotowane jako mały, powtarzalny pipeline do zadania `sendit`.

## Co tu jest

- `src/sendit_pipeline.py` - pobieranie dokumentacji, analiza obrazów, składanie deklaracji i wysyłka do `verify`
- `input.json` - dane wejściowe do zadania
- `cache/` - lokalna kopia dokumentacji tekstowej
- `assets/` - pobrane pliki graficzne
- `output/` - analiza obrazu, finalna deklaracja, payload i odpowiedź z `verify`

## Szybki kontekst

- Główny dokument: `cache/index.md`
- Wzór deklaracji: `cache/zalacznik-E.md`
- Dopłaty / wagony: `cache/dodatkowe-wagony.md`
- Mapa i skróty: `cache/zalacznik-F.md`, `cache/zalacznik-G.md`
- Trasy wyłączone: `assets/trasy-wylaczone.png` + `output/image_analysis.json`

## Ustalona logika dla tego przypadku

- Trasa `Gdańsk -> Żarnowiec` to `X-01`
- Żarnowiec przyjmuje tylko kategorie `A` lub `B`
- Budżet `0 PP` wymusza przesyłkę finansowaną przez System
- Dla `kasety z paliwem do reaktora` solver wybiera kategorię `A`
- Masa `2800 kg` wymaga `4` dodatkowych wagonów
- `KWOTA DO ZAPŁATY` pozostaje `0 PP`
- `UWAGI SPECJALNE` muszą zostać puste

## Jak uruchomić ponownie

1. Uzupełnij `input.json`.
   Placeholder `task_api_key` może zostać nadpisany przez `AI_devs4_solutions/local.secrets.json`.
2. Pobierz dokumentację:

```powershell
python .\src\sendit_pipeline.py download --workdir .
```

3. Przeanalizuj obrazy przez Gemini:

```powershell
python .\src\sendit_pipeline.py analyze-images --workdir . --gemini-api-key "<GEMINI_API_KEY>"
```

4. Złóż i zwaliduj deklarację lokalnie:

```powershell
python .\src\sendit_pipeline.py solve --workdir .
```

5. Wyślij do huba:

```powershell
python .\src\sendit_pipeline.py verify --workdir .
```

## Na co uważać przy reużyciu

- Pole `WDP` musi odzwierciedlać realną liczbę dodatkowych wagonów potrzebnych do przewozu, nawet jeśli koszt jest `0 PP`.
- Jeśli hub zwraca błąd biznesowy, poprawiaj logikę w `src/sendit_pipeline.py`, nie tylko ręczny tekst deklaracji.
- Jeśli pojawią się nowe obrazy w dokumentacji, najpierw rozszerz `analyze-images`, a dopiero potem solver.
- Jeśli zmieni się interpretacja kategorii, aktualizuj `classify_shipment()` i walidację razem.

## Ostatni poprawny wynik

- `output/verify_response.json` zawiera odpowiedź huba dla poprawnego zgłoszenia.

## Sekrety lokalne

- Prawdziwe klucze trzymaj w `AI_devs4_solutions/local.secrets.json`
- Repo zawiera tylko `local.secrets.json.example`
- Obsługiwane pola:
  - `ag3nts_api_key`
  - `gemini_api_key`
  - `s01e04_task_api_key`
