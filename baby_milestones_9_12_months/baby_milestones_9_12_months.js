"use strict";

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { imageSizingContain } = require("./pptxgenjs_helpers/image");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers/layout");
const { safeOuterShadow } = require("./pptxgenjs_helpers/util");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "OpenAI";
pptx.subject = "Baby milestones from 9 to 12 months";
pptx.title = "Baby Milestones: 9 to 12 Months";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  lang: "en-US",
};

const OUT = path.join(__dirname, "baby_milestones_9_12_months.pptx");
const asset = (name) => path.join(__dirname, "assets", name);

const colors = {
  ink: "17324D",
  sub: "4D6277",
  peach: "F7E2D2",
  sand: "FFF7F0",
  coral: "EB8E72",
  teal: "7FB8AD",
  gold: "F2C46D",
  sky: "DDEDF7",
  mint: "DCEFE6",
  blush: "F8D9D3",
  white: "FFFFFF",
  navy: "12304A",
  panel: "FFFDF9",
  alert: "FFF0D9",
};

function addFullBleedBackground(slide, topColor, bottomColor) {
  slide.background = { color: topColor || bottomColor };
}

function addHeaderText(slide, title, subtitle, x = 0.7, y = 0.55, w = 6.1) {
  slide.addText(title, {
    x,
    y,
    w,
    h: 0.55,
    fontFace: "Arial",
    fontSize: 24,
    bold: true,
    color: colors.ink,
    margin: 0,
  });
  slide.addText(subtitle, {
    x,
    y: y + 0.7,
    w,
    h: 0.55,
    fontFace: "Arial",
    fontSize: 10.5,
    color: colors.sub,
    margin: 0,
  });
}

function addRoundedPanel(slide, x, y, w, h, fill, radius = 0.14) {
  slide.addText("", {
    x,
    y,
    w,
    h,
    shape: pptx.ShapeType.roundRect,
    rectRadius: radius,
    line: { color: fill, transparency: 100 },
    fill: { color: fill },
    shadow: safeOuterShadow("8A6E4B", 0.14, 45, 1.5, 1),
    margin: 0,
  });
}

function addBulletList(slide, items, x, y, w, h, color = colors.ink, size = 11) {
  slide.addText(
    items.map((text) => ({
      text,
      options: { bullet: { indent: 12 } },
    })),
    {
      x,
      y,
      w,
      h,
      fontFace: "Arial",
      fontSize: size,
      color,
      breakLine: false,
      paraSpaceAfterPt: 9,
      valign: "top",
      margin: 0.04,
    }
  );
}

function addMonthCard(slide, month, highlight, details, x, y, fill) {
  addRoundedPanel(slide, x, y, 1.85, 2.18, fill);
  slide.addText(month, {
    x: x + 0.16,
    y: y + 0.15,
    w: 0.7,
    h: 0.3,
    fontFace: "Arial",
    fontSize: 15,
    bold: true,
    color: colors.navy,
    margin: 0,
  });
  slide.addText(highlight, {
    x: x + 0.16,
    y: y + 0.53,
    w: 1.5,
    h: 0.45,
    fontFace: "Arial",
    fontSize: 12.5,
    bold: true,
    color: colors.ink,
    margin: 0,
  });
  slide.addText(details, {
    x: x + 0.16,
    y: y + 0.98,
    w: 1.5,
    h: 0.95,
    fontFace: "Arial",
    fontSize: 9.5,
    color: colors.sub,
    margin: 0,
    valign: "top",
  });
}

function addSkillCard(slide, title, items, x, y, fill) {
  addRoundedPanel(slide, x, y, 2.6, 1.76, fill);
  slide.addText(title, {
    x: x + 0.18,
    y: y + 0.16,
    w: 2,
    h: 0.28,
    fontFace: "Arial",
    fontSize: 13,
    bold: true,
    color: colors.ink,
    margin: 0,
  });
  addBulletList(slide, items, x + 0.14, y + 0.48, 2.25, 0.98, colors.sub, 9.5);
}

function addPill(slide, text, x, y, w, fill) {
  slide.addText(text, {
    x,
    y,
    w,
    h: 0.38,
    shape: pptx.ShapeType.roundRect,
    rectRadius: 0.18,
    fontFace: "Arial",
    fontSize: 10,
    bold: true,
    align: "center",
    valign: "mid",
    color: colors.navy,
    line: { color: fill, transparency: 100 },
    fill: { color: fill },
    margin: 0,
  });
}

function addFooter(slide) {
  slide.addText("Milestones vary within a normal range. Use patterns over time and talk with a pediatrician if you feel stuck or worried.", {
    x: 0.72,
    y: 7.08,
    w: 11.9,
    h: 0.22,
    fontFace: "Arial",
    fontSize: 8.5,
    color: "6B7785",
    italic: true,
    margin: 0,
    align: "left",
  });
}

function addSlideOne() {
  const slide = pptx.addSlide();
  addFullBleedBackground(slide, colors.sand, colors.sky);
  addHeaderText(
    slide,
    "Baby milestones: 9 to 12 months",
    "A quick, parent-friendly view of the big changes often seen in late infancy."
  );

  slide.addText("Many babies are becoming more mobile, more interactive, and more intentional with their hands during this stretch.", {
    x: 0.72,
    y: 1.9,
    w: 4.55,
    h: 0.62,
    fontFace: "Arial",
    fontSize: 16,
    color: colors.ink,
    margin: 0,
    valign: "mid",
  });

  addPill(slide, "Movement", 0.72, 3.0, 1.15, colors.mint);
  addPill(slide, "Pincer grasp", 1.97, 3.0, 1.45, colors.peach);
  addPill(slide, "First words", 3.55, 3.0, 1.32, colors.gold);

  slide.addImage({
    path: asset("timeline_journey.svg"),
    ...imageSizingContain(asset("timeline_journey.svg"), 7.15, 0.92, 5.15, 2.45),
  });

  addMonthCard(slide, "9 mo", "Gets around", "May sit without support, crawl, or scoot to reach people and toys.", 0.72, 3.45, colors.white);
  addMonthCard(slide, "10 mo", "Pulls up", "Often shifts from floor play to kneeling or standing while holding on.", 2.74, 3.45, colors.blush);
  addMonthCard(slide, "11 mo", "Cruises", "Moves sideways along furniture and uses fingers more precisely.", 4.76, 3.45, colors.white);
  addMonthCard(slide, "12 mo", "Shows intent", "May take first steps, point, wave, and use simple words like 'mama' or 'dada'.", 6.78, 3.45, colors.blush);

  addRoundedPanel(slide, 8.93, 3.45, 3.52, 2.18, "F6FBFD");
  slide.addText("What families often notice", {
    x: 9.15,
    y: 3.62,
    w: 2.6,
    h: 0.3,
    fontFace: "Arial",
    fontSize: 13,
    bold: true,
    color: colors.ink,
    margin: 0,
  });
  addBulletList(
    slide,
    [
      "Longer floor-play sessions with more curiosity.",
      "More frustration when a goal is blocked.",
      "Clearer preferences for favorite people and routines.",
    ],
    9.08,
    4.02,
    3.0,
    1.25,
    colors.sub,
    10
  );

  addFooter(slide);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function addSlideTwo() {
  const slide = pptx.addSlide();
  addFullBleedBackground(slide, colors.white, "F4FBF8");
  addHeaderText(
    slide,
    "Motor and hand skills are usually the headline changes",
    "Gross motor control and fine-motor precision often improve together from month to month."
  );

  slide.addImage({
    path: asset("motor_path.svg"),
    ...imageSizingContain(asset("motor_path.svg"), 0.7, 2.02, 4.15, 4.38),
  });

  addSkillCard(
    slide,
    "Body control",
    ["Sits steadily and pivots during play.", "Transitions in and out of positions with less help."],
    5.45,
    1.98,
    colors.sky
  );
  addSkillCard(
    slide,
    "Standing skills",
    ["Pulls to stand at furniture.", "Cruises along a couch or coffee table."],
    8.2,
    1.98,
    colors.peach
  );
  addSkillCard(
    slide,
    "Hands at work",
    ["Picks up tiny snacks with thumb and finger.", "Bangs, drops, and transfers objects on purpose."],
    5.45,
    3.74,
    colors.mint
  );
  addSkillCard(
    slide,
    "Early walking",
    ["Some babies take a few solo steps near 12 months.", "Others wait longer and still follow a healthy path."],
    8.2,
    3.74,
    "FFF3E8"
  );

  slide.addText("Helpful setup at home", {
    x: 5.5,
    y: 5.88,
    w: 2.05,
    h: 0.3,
    fontFace: "Arial",
    fontSize: 12.5,
    bold: true,
    color: colors.ink,
    margin: 0,
  });
  addPill(slide, "Barefoot time", 5.48, 6.28, 1.35, colors.gold);
  addPill(slide, "Low furniture", 6.95, 6.28, 1.45, colors.sky);
  addPill(slide, "Safe floor space", 8.56, 6.28, 1.58, colors.mint);
  addPill(slide, "Finger foods", 10.3, 6.28, 1.25, colors.peach);

  addFooter(slide);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function addSlideThree() {
  const slide = pptx.addSlide();
  addFullBleedBackground(slide, "FFFDF8", "FFF5EB");
  addHeaderText(
    slide,
    "Communication and social play become more purposeful",
    "This stage often brings more imitation, shared attention, and clear attempts to communicate needs."
  );

  addRoundedPanel(slide, 0.72, 1.95, 5.1, 4.58, colors.panel);
  slide.addText("Often seen between 9 and 12 months", {
    x: 0.98,
    y: 2.18,
    w: 2.9,
    h: 0.28,
    fontFace: "Arial",
    fontSize: 13.5,
    bold: true,
    color: colors.ink,
    margin: 0,
  });
  addBulletList(
    slide,
    [
      "Responds to their name and turns toward familiar voices.",
      "Uses gestures such as waving, reaching, or lifting arms to be picked up.",
      "Looks where you point and enjoys back-and-forth games like peekaboo.",
      "Babbles with speech-like rhythm and may start using 1 to 3 meaningful words.",
      "Shows object permanence by searching for a hidden toy.",
    ],
    0.96,
    2.62,
    4.45,
    2.7,
    colors.sub,
    10.5
  );
  addPill(slide, "Name response", 0.98, 5.56, 1.28, colors.sky);
  addPill(slide, "Pointing", 2.38, 5.56, 1.02, colors.peach);
  addPill(slide, "Peekaboo", 3.52, 5.56, 1.08, colors.gold);

  slide.addImage({
    path: asset("language_play.svg"),
    ...imageSizingContain(asset("language_play.svg"), 6.18, 1.8, 3.05, 3.2),
  });

  addRoundedPanel(slide, 9.45, 1.76, 2.95, 2.35, colors.alert);
  slide.addText("Check in sooner if you notice", {
    x: 9.68,
    y: 1.98,
    w: 2.3,
    h: 0.45,
    fontFace: "Arial",
    fontSize: 13,
    bold: true,
    color: colors.ink,
    margin: 0,
  });
  addBulletList(
    slide,
    [
      "No interest in people or shared play.",
      "No babbling or no attempt to communicate.",
      "Very limited movement progress or loss of a skill already gained.",
    ],
    9.63,
    2.58,
    2.3,
    1.28,
    colors.ink,
    9.4
  );

  addRoundedPanel(slide, 6.05, 5.22, 6.35, 1.32, "F7EDE3");
  slide.addText("Best support: talk during routines, read short books, offer safe objects to explore, and celebrate small attempts instead of chasing perfect timing.", {
    x: 6.28,
    y: 5.52,
    w: 5.9,
    h: 0.72,
    fontFace: "Arial",
    fontSize: 11,
    color: colors.ink,
    margin: 0,
    valign: "mid",
  });

  addFooter(slide);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

addSlideOne();
addSlideTwo();
addSlideThree();

pptx.writeFile({ fileName: OUT });
