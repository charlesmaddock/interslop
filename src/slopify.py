#!/usr/bin/env python3
"""
slopify.py — fork an Inter .ttf into an "InterSlop" .ttf where U+2014 (em dash)
and U+2013 (en dash) render as the lowercase letterforms "slop", composed and
scaled to fit the original glyph advance widths.

Usage:
    python slopify.py <input.ttf> <output.ttf>

Requires: fonttools (pip install fonttools)
"""

import sys
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform


# Empirically tuned for Inter's 2048 UPM. The em dash sits at y=553–719;
# we centre the lowercase x-height body on the midpoint of that range so
# "slop" reads as a small word floating where the bar used to be.
EM_DASH_MID_Y = 636
H_PADDING_FRACTION = 0.06  # 6% horizontal padding on each side of the word


def slopify(src_path: str, dst_path: str) -> None:
    font = TTFont(src_path)
    cmap = font.getBestCmap()
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    glyph_set = font.getGlyphSet()
    xheight = font["OS/2"].sxHeight or 1118

    em_aw = hmtx["emdash"][0]
    en_aw = hmtx["endash"][0]

    letters = [cmap[ord(c)] for c in "slop"]
    letter_aws = [hmtx[g][0] for g in letters]
    word_aw_unscaled = sum(letter_aws)

    def build_word(target_aw: int):
        """Compose s+l+o+p into a single glyph that fills target_aw."""
        pen = TTGlyphPen(glyph_set)
        pad = int(target_aw * H_PADDING_FRACTION)
        scale = (target_aw - 2 * pad) / word_aw_unscaled
        baseline_y = int(EM_DASH_MID_Y - (xheight * scale) / 2)
        x = pad
        for gname, aw in zip(letters, letter_aws):
            t = Transform().translate(x, baseline_y).scale(scale)
            glyph_set[gname].draw(TransformPen(pen, t))
            x += aw * scale
        return pen.glyph()

    glyf["emdash"] = build_word(em_aw)
    glyf["endash"] = build_word(en_aw)

    # Rename the family so it installs side-by-side with Inter
    # (without colliding on family-name lookup).
    for record in font["name"].names:
        old = record.toUnicode()
        new = None
        if record.nameID == 1:                          # Family Name
            new = old + " Slop"
        elif record.nameID == 4:                        # Full Name
            new = old.replace("Inter", "Inter Slop") if "Inter" in old else old + " Slop"
        elif record.nameID == 6:                        # PostScript Name
            new = old.replace("Inter", "InterSlop") if "Inter" in old else old + "Slop"
        elif record.nameID == 16:                       # Typographic Family
            new = old + " Slop"
        if new is not None:
            if record.platformID == 3:
                record.string = new.encode("utf-16-be")
            else:
                record.string = new.encode("mac_roman", errors="ignore")

    font.save(dst_path)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    slopify(argv[1], argv[2])
    print(f"wrote {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
