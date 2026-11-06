#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inkex
from inkex import Layer, TextElement, Group, Rectangle
from lxml import etree

# ------------------------------------------------------------
# CONFIG (non-exposés)
# ------------------------------------------------------------

COLUMNS = 14
CELL_W = 12
CELL_H = 13
ADVANCE_DEFAULT = 10
METRIC_HEIGHT = 10

# ------------------------------------------------------------
# CHARSET
# ------------------------------------------------------------

CHARSET = [
    "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".",
    "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<",
    "=", ">", "?", "@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X",
    "Y", "Z", "[", "\\", "]", "^", "_", "`", "a", "b", "c", "d", "e", "f",
    "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
    "u", "v", "w", "x", "y", "z", "{", "|", "}", "~", "¡", "¢", "£", "¥",
    "¦", "§", "¨", "©", "ª", "«", "¬", "®", "¯", "°", "±", "²", "³", "´",
    "µ", "¶", "·", "¸", "¹", "º", "»", "¼", "½", "¾", "¿", "À", "Á", "Â",
    "Ã", "Ä", "Å", "Æ", "Ç", "È", "É", "Ê", "Ë", "Ì", "Í", "Î", "Ï", "Ð",
    "Ñ", "Ò", "Ó", "Ô", "Õ", "Ö", "Ø", "Ù", "Ú", "Û", "Ü", "Ý", "Þ", "ß",
    "à", "á", "â", "ã", "ä", "å", "æ", "ç", "è", "é", "ê", "ë", "ì", "í",
    "î", "ï", "ð", "ñ", "ò", "ó", "ô", "õ", "ö", "ø", "ù", "ú", "û", "ü",
    "ý", "þ", "ÿ", "Ā", "ā", "Ă", "ă", "Ą", "ą", "Ć", "ć", "Ĉ", "ĉ", "Ċ",
    "ċ", "Č", "č", "Ď", "ď", "Đ", "đ", "Ē", "ē", "Ĕ", "ĕ", "Ė", "ė", "Ę",
    "ę", "Ě", "ě", "Ĝ", "ĝ", "Ğ", "ğ", "Ġ", "ġ", "Ģ", "ģ", "Ĥ", "ĥ", "Ħ",
    "ħ", "Ĩ", "ĩ", "Ī", "ī", "Ĭ", "ĭ", "Į", "į", "İ", "ı", "Ĳ", "ĳ", "Ĵ",
    "ĵ", "Ķ", "ķ", "ĸ", "Ĺ", "ĺ", "Ļ", "ļ", "Ľ", "ľ", "Ŀ", "ŀ", "Ł", "ł",
    "Ń", "ń", "Ņ", "ņ", "Ň", "ň", "ŉ", "Ŋ", "ŋ", "Ō", "ō", "Ŏ", "ŏ", "Ő",
    "ő", "Œ", "œ", "Ŕ", "ŕ", "Ŗ", "ŗ", "Ř", "ř", "Ś", "ś", "Ŝ", "ŝ", "Ş",
    "ş", "Š", "š", "Ţ", "ţ", "Ť", "ť", "Ŧ", "ŧ", "Ũ", "ũ", "Ū", "ū", "Ŭ",
    "ŭ", "Ů", "ů", "Ű", "ű", "Ų", "ų", "Ŵ", "ŵ", "Ŷ", "ŷ", "Ÿ", "Ź", "ź",
    "Ż", "ż", "Ž", "ž", "€",
]

# ------------------------------------------------------------
# EXTENSION
# ------------------------------------------------------------

INK_NS = "http://www.inkscape.org/namespaces/inkscape"

class GlyphGridEffect(inkex.Effect):

    def add_arguments(self, pars):
        pars.add_argument("--font-family", type=str, dest="font_family", default="Arial")

    def effect(self):
        font_family = self.options.font_family
        font_size   = 10

        root = self.document.getroot()

        glyph_layer   = self._make_layer(root, "Glyphs")
        metrics_layer = self._make_layer(root, "Metrics")

        for idx, ch in enumerate(CHARSET):
            row = idx // COLUMNS
            col = idx % COLUMNS
            gx  = col * CELL_W
            gy  = row * CELL_H + METRIC_HEIGHT
            code = ord(ch)

            # --- glyph text ---
            t = etree.SubElement(glyph_layer, inkex.addNS("text", "svg"))
            t.set("id",f"glyph_U+{code:04X}_{ch}")
            t.set(inkex.addNS("label", "inkscape"), ch)
            t.set("x",                          str(gx))
            t.set("y",                          str(gy))
            t.set("font-family",                font_family)
            t.set("font-size",                  str(font_size))
            t.set("dominant-baseline",          "alphabetic")
            t.text = ch

            # --- metrics group + rect ---
            r = etree.SubElement(metrics_layer, inkex.addNS("rect", "svg"))
            r.set("transform", f"translate({gx},{gy})")
            r.set("id", f"metrics_U+{code:04X}_{ch}")
            r.set(inkex.addNS("label", "inkscape"), f"metrics_U+{code:04X}_{ch}")
            r.set("x",            "0")
            r.set("y",            str(-METRIC_HEIGHT))
            r.set("width",        str(ADVANCE_DEFAULT))
            r.set("height",       str(METRIC_HEIGHT))
            r.set("fill",         "none")
            r.set("stroke",       "#ff0000")
            r.set("stroke-width", "0.2")

    def _make_layer(self, root, label):
        g = etree.SubElement(root, inkex.addNS("g", "svg"))
        g.set(inkex.addNS("label",     "inkscape"), label)
        g.set(inkex.addNS("groupmode", "inkscape"), "layer")
        return g


if __name__ == "__main__":
    GlyphGridEffect().run()
