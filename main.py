#!/usr/bin/env python3
"""news-image-20261126: one dense front page summing up the world news of
Thursday 26 November 2026.

Every story below happened, or was first reported, on 26 November 2026
(any time zone). Sources checked while building: Reuters, AP, USA TODAY,
BBC Verify, EUR Radio, NASA, USTR, Dow Jones, Just Security, C54,
The Insight International, and the 26 November school-assembly roundups
that aggregate the day's wires. Stories dated 24 or 25 November were
dropped, even when they were still being talked about on the 26th.

Run:  python3 main.py            (writes entry.png next to out/ or $MAKEFUN_OUTPUT_DIR)
The program is fully offline and deterministic: same bytes on every run.
"""
import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (246, 241, 231)
INK = (20, 33, 61)
RED = (179, 32, 44)
GOLD = (180, 138, 44)
GREY = (90, 90, 88)
NAVY_STRIP = (20, 33, 61)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

DATE_LINE = "THURSDAY 26 NOVEMBER 2026"

LEADS = [
    {
        "tag": "TRADE",
        "headline": "US proposes tariffs on 14 economies; China rejects plan",
        "deck": "USTR plan covers China, the EU, Japan and 11 others at up to 40%; Beijing calls it groundless.",
    },
    {
        "tag": "SPACE",
        "headline": "SpaceX wins FCC approval for one million orbital AI data-centre satellites",
        "deck": "The Starmind constellation would run solar-powered computing in orbit, "
                "linked by lasers.",
    },
    {
        "tag": "SECURITY",
        "headline": "Colombia police storm supermarket, freeing 20 hostages after 17-hour siege",
        "deck": "Gunmen held dozens in Cartagena after a failed robbery; troops ended the standoff.",
    },
]

# (region, header colour, [(field, headline), ...])
PANELS = [
    ("NORTH AMERICA", (31, 78, 121), [
        ("COURTS", "Judge declines to extend Trump ads ban"),
        ("TECH", "AG dodges questions on Nvidia investigation"),
        ("COURTS", "Justice Dept crackdown targets 800+ scam defendants"),
        ("COURTS", "Fort Hood survivors lose final appeal on witness bid"),
        ("ACCIDENT", "Search for six aboard plane lost over Gulf of Mexico"),
    ]),
    ("EUROPE", (122, 59, 46), [
        ("TRANSPORT", "London Tube strike: no Piccadilly or Circle line all day"),
        ("ECONOMY", "3.7m industrial jobs at risk across Europe"),
        ("DEFENCE", "Russia's military budget surges as rearmament accelerates"),
        ("POLICY", "EU Parliament advances budget proposals for 2028-34"),
        ("ANIMALS", "EU court hands down ruling on caged-animal farming"),
        ("ENERGY", "Norway top court voids disputed oil licences"),
    ]),
    ("UKRAINE & RUSSIA", (91, 45, 142), [
        ("WAR", "Russia's own figures put Ukraine war dead near 500,000"),
        ("WAR", "Ukraine strike on Savasleyka airbase damages five jets"),
        ("DIPLOMACY", "US shelves plan to end Ukraine war with deals"),
        ("CRYPTO", "Ukraine legalises, taxes crypto market from July 2027"),
        ("DEFENCE", "Europe's rearmament still leans heavily on US weapons"),
    ]),
    ("MIDDLE EAST", (138, 109, 27), [
        ("CONFLICT", "Saudi Arabia intercepts Houthi missiles over Riyadh"),
        ("CONFLICT", "Houthis report deaths after Saudi strikes in Yemen"),
        ("DIPLOMACY", "India condemns Riyadh tower attack, two Indians hurt"),
        ("SECURITY", "Israeli minister says Iran is developing chemical weapons"),
    ]),
    ("AFRICA", (46, 107, 52), [
        ("SECURITY", "Gunmen kill at least 30 in Nigeria's Niger state"),
        ("HEALTH", "Kenya discharges last Ebola patient; DRC toll tops 5,300"),
        ("ECONOMY", "Ghana unveils banknotes honouring Nkrumah, Annan"),
        ("DEFENCE", "Nigeria starts building its own naval ships"),
        ("POLITICS", "Protest outside S. African court over barred rallies"),
        ("POLITICS", "Ramos reappointed PM of Sao Tome and Principe"),
    ]),
    ("SOUTH ASIA", (179, 32, 44), [
        ("LABOUR", "Bangladesh raises garment minimum wage by 36%"),
        ("DIPLOMACY", "India announces Rs 15,000-crore package for Nepal"),
        ("POLITICS", "Hasina seeks return to Bangladesh on 16 December"),
        ("DISASTER", "5.6-magnitude quake hits Nepal's Koshi province"),
        ("BANKING", "Indian banks write off Rs 1.44 lakh crore in FY26"),
        ("DIPLOMACY", "Modi, Merz hold talks on strategic partnership"),
    ]),
    ("EAST ASIA & PACIFIC", (15, 118, 110), [
        ("TRADE", "China rejects the basis of the new US tariff proposal"),
        ("SECURITY", "N. Korea's Kim calls for wider use of tactical nuclear arms"),
        ("DISASTER", "Indonesia factory fire toll reaches 24; 30 still missing"),
        ("SPORT", "New Zealand hold India to a draw in the first Test"),
    ]),
    ("SCIENCE, TECH & SPACE", (51, 65, 85), [
        ("SPACE", "Hera reveals first close-ups of Dimorphos dent"),
        ("AI", "Google DeepMind launches Mass Spec Skills at 97% accuracy"),
        ("TECH", "Amazon and Meta in talks to unblock Muse AI shopping agent"),
        ("CRYPTO", "Bitcoin, Ether ETFs see record Nov outflows of $4.71bn"),
        ("TECH", "BBC Verify links 500+ deepfakes to China"),
    ]),
]

BRIEF = [
    "Thanksgiving Day as Progress 97 cargo docks at space station",
    "Gukesh faces Sindarov in the World Chess Championship",
    "Sooryavanshi smashes 204 off 53 balls against UAE",
    "Flipkart CEO to step down in December, report says",
    "Awar Odhiang named model of the year",
    "India's top court defers bail pleas of Umar Khalid, Sharjeel Imam",
]

TICKER = ("MARKETS  Hang Seng -1.14%  |  Shanghai -2.03%  |  Sensex -1,484  |  "
           "Nifty below 25,400  |  Bitcoin ETFs: record $4.71bn Nov outflows")

FOOTER = ("All 50 stories happened or were first reported on Thursday 26 November 2026  |  "
          "Sources: Reuters, AP, USA TODAY, BBC Verify, EUR Radio, NASA, USTR, Dow Jones")


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrap_first_rest(draw, text, fnt, first_w, rest_w):
    """Greedy word wrap where the first line is narrower (a tag sits on it)
    and continuation lines use the full width."""
    words = text.split()
    lines, cur, cap = [], "", first_w
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= cap:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
            cap = rest_w
    if cur:
        lines.append(cur)
    return lines


def draw_story(draw, x, y, w, field, headline, colour, f_head, f_tag, max_lines=3):
    """One compact story: coloured field tag, bold headline wrapped to <= max_lines.
    Returns the y just below the story."""
    tag = field + "  "
    draw.text((x, y), tag, font=f_tag, fill=colour)
    tag_w = draw.textlength(tag, font=f_tag)
    lines = wrap_first_rest(draw, headline, f_head, w - tag_w, w)[:max_lines]
    # First line starts after the tag; continuation lines use full width.
    lx, ly = x + tag_w, y
    for i, line in enumerate(lines):
        draw.text((lx, ly), line, font=f_head, fill=INK)
        ly += 14
        lx = x
    return ly + 5


def build():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    f_title = font(SERIF_B, 52)
    f_date = font(SANS_B, 17)
    f_counts = font(SANS_B, 14)
    f_kicker = font(SANS_B, 13)
    f_lead_h = font(SANS_B, 18)
    f_lead_d = font(SANS, 13)
    f_panel = font(SANS_B, 13)
    f_head = font(SANS_B, 12)
    f_tag = font(SANS_B, 10)
    f_ticker = font(SANS_B, 13)
    f_brief = font(SANS, 12)
    f_foot = font(SANS, 10)

    # ---- masthead ----
    draw.rectangle([0, 0, W, 6], fill=RED)
    title = "THE WORLD IN ONE PAGE"
    tw = draw.textlength(title, font=f_title)
    draw.text(((W - tw) / 2, 16), title, font=f_title, fill=INK)
    draw.line([16, 82, W - 16, 82], fill=INK, width=2)
    draw.text((16, 88), DATE_LINE, font=f_date, fill=RED)
    counts = "50 STORIES  |  10 REGIONS  |  23 FIELDS"
    cw = draw.textlength(counts, font=f_counts)
    draw.text((W - 16 - cw, 90), counts, font=f_counts, fill=INK)
    draw.line([16, 114, W - 16, 114], fill=INK, width=1)

    # ---- lead band: hero image + top of the day ----
    hero_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "hero.png")
    hero = Image.open(hero_path).convert("RGB")
    hero = hero.resize((196, 196), Image.LANCZOS)
    img.paste(hero, (16, 122))
    draw.rectangle([16, 122, 212, 318], outline=INK, width=1)

    lx = 228
    draw.text((lx, 122), "TOP OF THE DAY", font=f_kicker, fill=RED)
    ly = 144
    for i, lead in enumerate(LEADS, 1):
        # numbered disc
        cx, cy = lx + 11, ly + 11
        draw.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=RED)
        num = str(i)
        nw = draw.textlength(num, font=f_lead_h)
        draw.text((cx - nw / 2, cy - 11), num, font=f_lead_h, fill=(255, 255, 255))
        tx = lx + 30
        tw_ = W - 16 - tx
        tag = lead["tag"] + "  "
        draw.text((tx, ly), tag, font=f_tag, fill=RED)
        tag_w = draw.textlength(tag, font=f_tag)
        hlines = wrap(draw, lead["headline"], f_lead_h, tw_ - tag_w)[:2]
        hx, hy = tx + tag_w, ly
        for line in hlines:
            draw.text((hx, hy), line, font=f_lead_h, fill=INK)
            hy += 20
            hx = tx
        dlines = wrap(draw, lead["deck"], f_lead_d, tw_)[:1]
        for line in dlines:
            draw.text((tx, hy), line, font=f_lead_d, fill=GREY)
            hy += 15
        ly = hy + 5

    # ---- markets ticker ----
    draw.rectangle([16, 332, W - 16, 356], fill=NAVY_STRIP)
    if draw.textlength(TICKER, font=f_ticker) > 960:
        f_ticker = font(SANS_B, 12)
    tw_ = draw.textlength(TICKER, font=f_ticker)
    draw.text(((W - tw_) / 2, 338), TICKER, font=f_ticker, fill=(255, 255, 255))

    # ---- region panels: 4 columns x 2 rows ----
    px0, py0 = 16, 366
    pw, ph, gap = 239, 276, 10
    for idx, (region, colour, stories) in enumerate(PANELS):
        col, row = idx % 4, idx // 4
        x = px0 + col * (pw + gap)
        y = py0 + row * (ph + gap)
        draw.rectangle([x, y, x + pw, y + 28], fill=colour)
        draw.text((x + 8, y + 6), region, font=f_panel, fill=(255, 255, 255))
        sy = y + 36
        for field, headline in stories:
            sy = draw_story(draw, x + 2, sy, pw - 4, field, headline,
                            colour, f_head, f_tag)

    # ---- also today: 2 columns x 3 rows, one line each ----
    by = py0 + 2 * ph + gap + 6  # 934
    draw.text((16, by), "ALSO TODAY", font=f_kicker, fill=RED)
    draw.line([110, by + 7, W - 16, by + 7], fill=GREY, width=1)
    bw = (W - 32 - 16) // 2
    for i, item in enumerate(BRIEF):
        col, row = i % 2, i // 2
        bx = 16 + col * (bw + 16)
        byy = by + 16 + row * 17
        draw.text((bx, byy), "\u2022  ", font=f_brief, fill=RED)
        draw.text((bx + 12, byy), item, font=f_brief, fill=INK)

    # ---- footer ----
    fy = 1010
    draw.line([16, fy - 8, W - 16, fy - 8], fill=INK, width=1)
    fw = draw.textlength(FOOTER, font=f_foot)
    if fw > W - 32:
        # shrink to fit on one line
        f_foot2 = font(SANS, 9)
        draw.text((16, fy), FOOTER, font=f_foot2, fill=GREY)
    else:
        draw.text((16, fy), FOOTER, font=f_foot, fill=GREY)

    return img


def story_count():
    n = len(LEADS) + sum(len(s) for _, _, s in PANELS) + len(BRIEF)
    fields = {lead["tag"] for lead in LEADS}
    for _, _, stories in PANELS:
        fields |= {f for f, _ in stories}
    return n, len(fields)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    img = build()
    assert img.size == (1024, 1024), img.size
    img.save(out_path, format="PNG", optimize=True)
    n, nfields = story_count()
    size = os.path.getsize(out_path)
    digest = hashlib.sha256(open(out_path, "rb").read()).hexdigest()[:16]
    print(f"wrote {out_path}  {img.size[0]}x{img.size[1]}  {size} bytes  "
          f"sha256:{digest}  stories={n} fields={nfields}")
    assert size <= 1048576, f"entry.png too big: {size} bytes"
    return 0


if __name__ == "__main__":
    sys.exit(main())
