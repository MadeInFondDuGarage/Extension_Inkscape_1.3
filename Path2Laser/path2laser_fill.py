#!/usr/bin/env python
# coding=utf-8

################################################################################
#
# Remplissage des formes pleines pour la gravure laser
#
# Module indépendant : il agit uniquement sur le dessin Inkscape et n'utilise rien des autres fichiers
# de path2laser. Il est appelé par path2laser_gcode.py depuis l'onglet "Remplissage".
# Idée de départ : extension hatch_fill (Eggbot), le code est réécrit pour le laser.
#
# Principe :
#   - sans sélection, toutes les formes visibles du dessin ayant un fond sont remplies,
#     avec une sélection, seulement les formes sélectionnées (et le contenu des groupes sélectionnés)
#   - le fond de la forme est remplacé par un chemin de remplissage, placé juste après la forme :
#       trait de la couleur du fond (opacité du fond, réduite de x%), épaisseur = taille du point laser
#   - le fond de la forme d'origine est enlevé (fill:none), son contour n'est pas modifié
#   - 2 modes :
#       "hatch"  : hachures parallèles avec un angle, elles vont jusqu'au bord de la forme
#       "offset" : contours successifs décalés vers l'intérieur, le premier à une demi écartement du bord
#   - l'écartement entre 2 chemins est donné en % de la taille du point laser (100 = traits jointifs)
#   - la règle de remplissage (fill-rule) de la forme est respectée pour les hachures
#   - limites du mode "offset" : une zone plus étroite que l'écartement n'est pas remplie, et les sous-chemins
#     qui se chevauchent ne sont pas fusionnés (utiliser des trous en sens contraire)
#
################################################################################
import math

import numpy as np

import inkex
from inkex import PathElement

ATTR_IGNORE = "Path2Laser"  # éléments créés par path2laser (orientation, aperçu) : jamais remplis
TOLERANCE_COURBE_MM = 0.01  # précision de la transformation des courbes en segments
MAX_LIGNES = 100000  # sécurité : nombre maxi de hachures par forme
LONGUEUR_MINI = 0.1  # longueur mini d'une hachure, en fraction de l'écartement
FORMES = ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line")
NON_GEREES = ("text", "use", "image")


################################################################################
#
# Point d'entrée
#   svg          : racine du document
#   angle        : angle des hachures en degrés, sens trigonométrique à l'écran, 0 = horizontal
#   spot_mm      : taille du point laser en mm
#   ecart_pc     : écartement entre les chemins en % de la taille du point
#   reduction_pc : réduction de la puissance (opacité) en %
#   couleur_ok   : fonction(couleur inkex) -> bool, pour ne remplir que certaines couleurs (None = toutes)
# Retourne un dictionnaire : formes remplies, ignorées (couleur), non gérées, trop fines, chemins créés
#
################################################################################
def remplir(svg, angle, spot_mm, ecart_pc, reduction_pc, couleur_ok=None):
    stats = {"remplis": 0, "couleur": 0, "non_gere": 0, "vide": 0, "chemins": 0, "limite": 0}

    spot = svg.unittouu("{}mm".format(spot_mm))
    ecart = spot * max(ecart_pc, 1.0) / 100.0
    tolerance = svg.unittouu("{}mm".format(TOLERANCE_COURBE_MM))
    facteur_opacite = 1.0 - min(max(reduction_pc, 0.0), 100.0) / 100.0

    for noeud in _a_traiter(svg):
        if _balise(noeud) in NON_GEREES:
            if _couleur_fond(noeud) is not None:
                stats["non_gere"] += 1
            continue
        couleur = _couleur_fond(noeud)
        if couleur is None:
            continue
        if couleur_ok is not None and not couleur_ok(couleur):
            stats["couleur"] += 1
            continue
        style = _style(noeud)
        opacite = _nombre(style.get("fill-opacity"), 1.0)
        regle = str(style.get("fill-rule", "nonzero")).strip().lower()

        polygones = _polygones(noeud, tolerance)
        traces, limite = _traces_hachures(polygones, ecart, angle, regle)
        stats["limite"] += 1 if limite else 0
        if not traces:
            stats["vide"] += 1
            continue

        _ajouter_chemin(svg, noeud, traces, couleur, opacite * facteur_opacite, spot)
        stats["remplis"] += 1
        stats["chemins"] += len(traces)
    return stats


################################################################################
#
# Sélection des formes
#
################################################################################
def _a_traiter(svg):
    """formes visibles à remplir : la sélection si elle existe, sinon tout le document"""
    depart = list(svg.selected.values()) if len(svg.selected) > 0 else [svg]
    vus = set()
    for racine in depart:
        for noeud in _parcourir(racine):
            if id(noeud) not in vus:
                vus.add(id(noeud))
                yield noeud


def _parcourir(noeud):
    if not isinstance(noeud.tag, str) or noeud.get(ATTR_IGNORE) is not None:
        return
    if _masque(noeud):
        return
    balise = _balise(noeud)
    if balise in FORMES or balise in NON_GEREES:
        yield noeud
    elif balise in ("g", "svg"):
        for enfant in noeud:
            yield from _parcourir(enfant)


def _balise(noeud):
    return noeud.tag.split("}")[-1] if isinstance(noeud.tag, str) else ""


def _masque(noeud):
    """invisible : lui même ou un de ses parents a display:none"""
    el = noeud
    while el is not None and isinstance(el.tag, str):
        if str(inkex.Style(el.get("style", "")).get("display", "")).strip() == "none" or el.get("display") == "none":
            return True
        el = el.getparent()
    return False


################################################################################
#
# Style de la forme
#
################################################################################
def _style(noeud):
    try:
        return noeud.specified_style()
    except AttributeError:
        return noeud.style


def _nombre(valeur, defaut):
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return defaut


def _couleur_fond(noeud):
    """couleur du fond (objet Color) ou None s'il n'y a pas de fond plein, ni de fond opaque"""
    style = _style(noeud)
    fond = style.get("fill")
    if fond is None:
        return None
    fond = str(fond).strip()
    if fond in ("", "none", "inherit", "transparent") or fond.startswith("url("):
        return None
    if _nombre(style.get("fill-opacity"), 1.0) <= 0:
        return None
    try:
        return inkex.Color(fond)
    except Exception:
        return None


################################################################################
#
# Forme -> liste de polygones (tableaux numpy (n,2)) en coordonnées du document
# Tous les sous-chemins sont considérés comme fermés, comme pour un remplissage SVG
#
################################################################################
def _polygones(noeud, tolerance):
    try:
        chemin = noeud.path
    except Exception:
        chemin = noeud.to_path_element().path
    csp = chemin.transform(noeud.composed_transform()).to_superpath()

    polygones = []
    for sous_chemin in csp:
        points = [tuple(sous_chemin[0][1])]
        for a, b in zip(sous_chemin, sous_chemin[1:]):
            points += _aplatir(a[1], a[2], b[0], b[1], tolerance)
        poly = np.array(points, dtype=float)
        poly = _nettoyer(poly)
        if len(poly) >= 3:
            polygones.append(poly)
    return polygones


def _aplatir(p0, p1, p2, p3, tolerance):
    """courbe de bézier cubique -> points (sans le point de départ)"""
    if tuple(p1) == tuple(p0) and tuple(p2) == tuple(p3):
        return [tuple(p3)]
    ecart = max(math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1]),
                math.hypot(p1[0] - 2 * p2[0] + p3[0], p1[1] - 2 * p2[1] + p3[1]))
    n = int(min(200, max(1, math.ceil(math.sqrt(0.75 * ecart / max(tolerance, 1e-9))))))
    resultat = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        resultat.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                         u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return resultat


def _nettoyer(poly):
    """enlève les points en double, et le dernier point s'il est égal au premier"""
    if len(poly) < 2:
        return poly
    garde = np.ones(len(poly), dtype=bool)
    garde[1:] = np.hypot(*(poly[1:] - poly[:-1]).T) > 1e-9
    poly = poly[garde]
    if len(poly) > 1 and math.hypot(*(poly[0] - poly[-1])) <= 1e-9:
        poly = poly[:-1]
    return poly


################################################################################
#
# Création du chemin de remplissage, placé juste après la forme, fond de la forme enlevé
# Les points sont écrits dans le repère du parent, comme la forme
#
################################################################################
def _ajouter_chemin(svg, noeud, traces, couleur, opacite, spot):
    parent = noeud.getparent()
    inverse = -parent.composed_transform()
    a, b, c, d, e, f = inverse.to_hexad()
    echelle = math.sqrt(abs(a * d - b * c)) or 1.0

    morceaux = []
    for trace, ferme in traces:
        pts = [(a * x + c * y + e, b * x + d * y + f) for x, y in trace]
        morceaux.append("M " + " L ".join("{:.4f},{:.4f}".format(x, y) for x, y in pts) + (" Z" if ferme else ""))

    identifiant = noeud.get("id") or "forme"
    style = {"fill": "none", "stroke": str(couleur), "stroke-width": "{:.5f}".format(spot * echelle),
             "stroke-opacity": "{:g}".format(round(opacite, 4))}
    remplissage = PathElement()
    remplissage.set("d", " ".join(morceaux))
    remplissage.set("style", str(inkex.Style(style)))
    nouvel_id = identifiant + "_hach"
    if nouvel_id in svg.get_ids():
        nouvel_id = svg.get_unique_id(nouvel_id)
    remplissage.set("id", nouvel_id)
    remplissage.set("inkscape:label", identifiant + "_hach")
    noeud.addnext(remplissage)

    # fond de la forme d'origine enlevé
    style_forme = inkex.Style(noeud.get("style", ""))
    style_forme["fill"] = "none"
    noeud.set("style", str(style_forme))
    if noeud.get("fill") is not None:
        del noeud.attrib["fill"]


################################################################################
#
# Mode hachures
# Retourne ([(points, fermé)], limite atteinte)
#
################################################################################
def _traces_hachures(polygones, ecart, angle, regle):
    if not polygones:
        return [], False
    a = math.radians(angle)
    e = np.array([math.cos(a), -math.sin(a)])  # direction des hachures (y vers le bas)
    n = np.array([math.sin(a), math.cos(a)])  # perpendiculaire

    sa, ta, sb, tb = [], [], [], []
    for poly in polygones:
        suivant = np.roll(poly, -1, axis=0)
        sa.append(poly @ e)
        ta.append(poly @ n)
        sb.append(suivant @ e)
        tb.append(suivant @ n)
    sa, ta, sb, tb = map(np.concatenate, (sa, ta, sb, tb))

    k0 = int(math.ceil(ta.min() / ecart - 0.5))
    k1 = int(math.floor(ta.max() / ecart - 0.5))
    limite = (k1 - k0 + 1) > MAX_LIGNES
    if limite:
        return [], True

    pair_impair = regle == "evenodd"
    segments = []  # (s début, s fin, t)
    for k in range(k0, k1 + 1):
        t = (k + 0.5) * ecart
        coupe = ((ta <= t) & (tb > t)) | ((tb <= t) & (ta > t))
        if not coupe.any():
            continue
        s = sa[coupe] + (t - ta[coupe]) * (sb[coupe] - sa[coupe]) / (tb[coupe] - ta[coupe])
        sens = np.where(tb[coupe] > ta[coupe], 1, -1)
        ordre = np.argsort(s, kind="stable")
        s, sens = s[ordre], sens[ordre]
        if pair_impair:
            for d0, d1 in zip(s[0::2], s[1::2]):  # un point sur 2 ouvre un intervalle, le suivant le ferme
                segments.append((d0, d1, t))
        else:
            cumul = 0
            debut = None
            for position, valeur in zip(s, sens):
                avant = cumul
                cumul += valeur
                if avant == 0 and cumul != 0:
                    debut = position
                elif avant != 0 and cumul == 0:
                    segments.append((debut, position, t))

    mini = ecart * LONGUEUR_MINI
    segments = [sg for sg in segments if sg[1] - sg[0] > mini]
    if not segments:
        return [], False

    s0 = np.array([sg[0] for sg in segments])
    s1 = np.array([sg[1] for sg in segments])
    tt = np.array([sg[2] for sg in segments])
    debuts = np.outer(s0, e) + np.outer(tt, n)
    fins = np.outer(s1, e) + np.outer(tt, n)
    return [([tuple(p), tuple(q)], False) for p, q in _enchainer_segments(debuts, fins)], False


def _enchainer_segments(debuts, fins):
    """plus proche voisin avec inversion du sens : retourne la liste des (début, fin) dans l'ordre de gravure"""
    n = len(debuts)
    libre = np.ones(n, dtype=bool)
    position = debuts[0]
    resultat = []
    for _ in range(n):
        d0 = np.where(libre, np.hypot(*(debuts - position).T), np.inf)
        d1 = np.where(libre, np.hypot(*(fins - position).T), np.inf)
        i0, i1 = int(np.argmin(d0)), int(np.argmin(d1))
        if d0[i0] <= d1[i1]:
            i, p, q = i0, debuts[i0], fins[i0]
        else:
            i, p, q = i1, fins[i1], debuts[i1]
        libre[i] = False
        resultat.append((p, q))
        position = q
    return resultat


