#!/usr/bin/env python

################################################################################
#
# Engraving
#
# LT Notes to self: See wiki.inkscape.org/wiki/index.php/PythonEffectTutorial
# To create anything in the Inkscape document, look at the XML editor for
# details of how such an element looks in XML, then follow this model.
# layer number n appears in XML as <svg:g id="layern" inkscape:label="layername">
#
# to create it, use
# Mylayer = self.svg.add(Layer.new('layername'))
#
# group appears in XML as <svg:g id="gnnnnn"> where nnnnn is a number
#
# to create it, use
# Mygroup = parent.add(Group(gcodetools="My group label")
# where parent may be the layer or a parent group. To get the parent group, you can use
# parent = self.selected_paths[layer][0].getparent()
################################################################################
import math
import os
import re
import sys

import numpy

import inkex
from inkex.bezier import bezierlength, bezierparameterize
from inkex import Transform, PathElement, TextElement, Tspan, Group, Layer

# >>> EVOLUTION ordonnancement : module séparé, doit être dans le même dossier que ce fichier
import path2laser_order
# <<< FIN EVOLUTION ordonnancement


################################################################################
#
# Styles and additional parameters
#
################################################################################

TAU = math.pi * 2

################################################################################
# Couleurs reconnues (en dur), modifier ici pour faire évoluer
# Un chemin est retenu si son canal choisi est >= COLOR_SEUIL et que les 2 autres sont < COLOR_SEUIL
# Index du canal dans to_rgba() : 0 = rouge, 1 = vert, 2 = bleu
# Le canal choisi sert aussi à faire varier la vitesse (voir pc_couleur)
# Les 2 canaux doivent être différents
################################################################################
COLOR_CHANNEL_GRAV = 2  # bleu = gravure
COLOR_CHANNEL_CUT = 0   # rouge = découpe
COLOR_SEUIL = 100
STRAIGHT_TOLERANCE = 0.0001 #0.0001 #tolérance pour passer en ligne
STRAIGHT_DISTANCE_TOLERANCE = 0.0001 #0.0001 

EMC_TOLERANCE_EQUAL = 0.0001 #0.1 #0.00001 #lier a la tolérance d'arc minimum a voir si il faudrait pas le remonter

options = {}


INTERSECTION_RECURSION_DEPTH = 100
INTERSECTION_TOLERANCE = 0.00001

MARKER_STYLE = {
        "biarc_style" : {
                'biarc0': { 'stroke': '#88f', 'fill': 'none',  'stroke-width':'0.1' },
                'biarc1':{ 'stroke': '#8f8', 'fill': 'none', 'stroke-width':'0.1' },
                'line':{ 'stroke': '#f88', 'fill': 'none','stroke-width':'0.1' },
                'area':{ 'stroke': '#777', 'fill': 'none', 'stroke-width':'0.1' },
            },
        "dxf_points":{ "stroke": "#ff0000", "fill": "#ff0000"},

    }

################################################################################
###
###        Class d'entrée du module
###
################################################################################

class Path2Laser(inkex.EffectExtension):

    def __init__(self):
        inkex.Effect.__init__(self)
        #Gravure
        self.arg_parser.add_argument("--grav-laser-speed", type=int,dest="grav_laser_speed", default="750",  help="Laser speed (mm/min)")
        self.arg_parser.add_argument("--grav-laser-power",  type=int,dest="grav_laser_power",  default="255",   help="S# is 256 or 10000 for full power")
        # >>> CORRECTION 6 : Z en float (avant : type=int)
        self.arg_parser.add_argument("--grav-Z",  type=float,dest="grav_Z",  default="0", help="Hauteur du Z")
        # <<< FIN CORRECTION 6
        self.arg_parser.add_argument("--grav-color",  dest="grav_color",  default="0x000000ff",   help="Color for engraving")

        #Decoupe
        self.arg_parser.add_argument("--cut-laser-speed", type=int,dest="cut_laser_speed", default="750",  help="Laser speed (mm/min)")
        self.arg_parser.add_argument("--cut-laser-power",  type=int,dest="cut_laser_power",  default="255",   help="S# is 256 or 10000 for full power")
        # >>> CORRECTION 6 : Z en float (avant : type=int)
        self.arg_parser.add_argument("--cut-Z",  type=float,dest="cut_Z",  default="0", help="Hauteur du Z")
        # <<< FIN CORRECTION 6
        self.arg_parser.add_argument("--cut-passes",  type=int,dest="cut_passes",  default="3", help="Quantity of passes")
        self.arg_parser.add_argument("--cut-pass-depth", type=float ,dest="cut_pass_depth", default="0.5",  help="Depth of laser cut")
        self.arg_parser.add_argument("--cut-color",  dest="cut_color",  default="0xff0000ff",   help="Color for cuting")

        #Gcode
        self.arg_parser.add_argument("--travel-speed",dest="travel_speed", default="3000", help="Travel speed (mm/min)")
        self.arg_parser.add_argument("--Gcode-start", dest="Gcode_start",default="",help="start gcode command")
        self.arg_parser.add_argument("--Gcode-end", dest="Gcode_end",default="",help="end gcode command")
        self.arg_parser.add_argument("--laser-on-command-grav", dest="laser_on_command_grav",default="M4",help="Laser gcode command")
        self.arg_parser.add_argument("--laser-on-command-cut", dest="laser_on_command_cut",default="M3",help="Laser gcode command")
        self.arg_parser.add_argument("--laser-off-command", dest="laser_off_command", default="M5", help="Laser gcode end command")
        self.arg_parser.add_argument("--unit", dest="unit", default="G21 (All units in mm)",        help="Units either mm or inches")
        self.arg_parser.add_argument("--power-delay",type=float , dest="power_delay", default=0,help="Laser power-on delay (ms)")

        #Fichier
        self.arg_parser.add_argument("-d","--directory",    dest="directory", default="/home/david/", help="Output directory")
        self.arg_parser.add_argument("-f","--filename",     dest="file", default="output.gcode", help="File name")
        # >>> EVOLUTION ordonnancement : case à cocher dans l'onglet Gcode
        self.arg_parser.add_argument("--order-before-gcode", type=inkex.Boolean, dest="order_before_gcode", default=False, help="Reorder layers and paths before the gcode")
        # <<< FIN EVOLUTION ordonnancement
        self.arg_parser.add_argument("--add-numeric-suffix-to-filename", type=inkex.Boolean, dest="add_numeric_suffix_to_filename", default=False, help="Add numeric suffix to file name")

        self.arg_parser.add_argument("--tab", dest="tab",   help="The selected UI-tab when OK was pressed")
        self.arg_parser.add_argument("--path-to-gcode-depth-function", dest="path_to_gcode_depth_function", default="zd", help="Path to gcode depth function.")
        self.arg_parser.add_argument("--biarc-tolerance", type=float, dest="biarc_tolerance",  default="1", help="Tolerance used when calculating biarc interpolation.")
        self.arg_parser.add_argument("--biarc-max-split-depth", type=int, dest="biarc_max_split_depth", default="5", help="Defines maximum depth of splitting while approximating using biarcs.")
        self.arg_parser.add_argument("--min-arc-radius", type=float, dest="min_arc_radius", default=".5", help="All arc having radius less than minimum will be considered as straight line")

       
################################################################################
###
###        Effect
###
###        Main function of Gcodetools class
###
################################################################################
    def effect(self) :

        global options
        options = self.options
        options.self = self
        options.doc_root = self.document.getroot()

        # This automatically calls any `tab_{tab_name_in_inx}` which in this
        # extension is A LOT of different functions. So see all method prefixed
        # with tab_ to find out what's supported here.

        #defnition de l'outils pour la gravure laser, version par défaut dans un dict
        #element par défaut
        self.tools = {
            "name": "Laser Engraver",
            "id": "Laser Engraver",
            "penetration feed": 3000,
            "feed": 3000,
            "gcode before path": "",
            "gcode after path": "",
            "Pass_in":1,
            "Pass_depth":0,
            "Z_start": 0,
                    }

        self.Zone_name={'Definition':'Path2Laser'}

        # >>> EVOLUTION ordonnancement
        # sur l'onglet Ordre on ne fait que réordonner, pas de gcode
        if str(self.options.tab).strip("\"'") == "Ordre":
            self.Ordonnancement()
            return
        # sur les autres onglets, on réordonne avant le gcode si la case est cochée
        if self.options.order_before_gcode:
            self.Ordonnancement()
        # <<< FIN EVOLUTION ordonnancement

        #apres la vérification de la préparation, si tout est ok on lance le precessus de creation
        if self.Preparation():
            self.Go_Gcode()

################################################################################
###
###        go gcode
###
###        Main function of Gcodetools class
###TODO
################################################################################
    def Preparation(self):
        #"Orientation points have not been defined! A default set of orientation points has been automatically added."),"warning")
        self.get_info()
    
        if self.orientation_points == {}:
            self.orientation(self.layers[min(0,len(self.layers)-1)] )
            self.error("Aucun point d'orientation present. Creation des éléments.","warning")
            return False
        return True
        
    def Go_Gcode(self):
        self.path_to_gcode()

    # >>> EVOLUTION ordonnancement
    def Ordonnancement(self):
        stats = path2laser_order.reordonner(self.svg, type_chemin)
        if stats["groupes"] == 0 and stats["chemins"] == 0:
            self.error("Ordonnancement : rien à modifier, l'ordre est déjà correct.", "info")
        else:
            self.error("Ordonnancement : {} calque(s)/groupe(s) et {} chemin(s) déplacé(s).".format(stats["groupes"], stats["chemins"]), "info")
    # <<< FIN EVOLUTION ordonnancement

################################################################################
#
# Path to Gcode
#
################################################################################
    def path_to_gcode(self):

        def point_to_point_d2(a, b):
            return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

        def sort_lines(lines):
            if len(lines) == 0:
                return []
            lines = [[key] + lines[key] for key in range(len(lines))]
            keys = [0]
            end_point = lines[0][3:]
            del lines[0]
            while len(lines) > 0:
                dist = [[point_to_point_d2(end_point, lines[i][1:3]), i] for i in range(len(lines))]
                i = min(dist)[1]
                keys.append(lines[i][0])
                end_point = lines[i][3:]
                del lines[i]
            return keys
    
        def sort_curves(curves):
            lines = []
            for curve in curves:
                lines += [curve[0][0][0] + curve[-1][-1][0]]
            return sort_lines(lines)
         

        if self.selected_paths == {} :
            paths = self.paths
            # self.error("No paths are selected! Trying to work on all available paths.")
        else:
            paths = self.selected_paths
        self.check_dir()
        gcode = ""
        comment="()"
        
        # >>> CORRECTION 5 : suppression des anciens aperçus avant d'en créer un nouveau (avant : un groupe de plus à chaque exécution)
        for old_preview in self.svg.xpath('//svg:g[@{}="Preview groups"]'.format(self.Zone_name['Definition'])):
            old_preview.getparent().remove(old_preview)
        # <<< FIN CORRECTION 5
        attr = {self.Zone_name['Definition']: "Preview groups"}
        PreviewGroups = self.svg.add(Group(**attr))
        PreviewGroups.label="Preview groups"
        
        for layer in self.layers:
            #je ne traite que les calques/groupes visible qui sont récuperer dans la partie get_infos()
            comment_layer=""
 
            if layer in paths:# la selection de l'état de visibilité des calques et groups ce fait sur la gestion des layers
                # transform simple path to get all var about orientation
                self.transform_csp([[[[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]]]], layer)

                #je fait un commentaire spécifique a bCNC pour chaque calque/groupe je ne prend que ceux qui on un label, donc définie par l'utilisateur
                curves = []
                if  layer.groupmode == "layer":
                    if layer.label != None: # je suis sur un calque
                        comment_layer= "\n(Block-name:" + layer.label +")\n"  #je prend le label si il existe
                    else:
                        comment_layer= "\n(Block-name:" + layer.get("id") +")\n" # sinon l'id pour les calque
                else:
                    if layer.label != None:
                        comment_layer= "\n(Block-name:" + layer.label +")\n"  #pour un groupe si il a un label utilisateur je le prend comme un block
                    else:
                        comment_layer= "\n((Group: " + layer.get("id") +"))\n" # sinon je fait un simple commentaire
                    
                for path in paths[layer]:
                    if "d" not in path.keys():
                        self.error("Warning: One or more paths do not have 'd' parameter, try to Ungroup (Ctrl+Shift+G) and Object to Path (Ctrl+Shift+C)!")
                        continue
                    csp = path.path.to_superpath()
                    csp = self.apply_transforms(path, csp)
                    id_ = path.get("id")

                    stroke = path.style('stroke')
                    stroke_opacity = round(path.style('stroke-opacity'),2) # pour la puissance et j'arrondi
                    display=path.style('display')
                       
                    comment_path="\n(("+path.get("id")+"))\n" #pour chaque chemin je met 2 parenthese pour simplifier la mise en commentaire en masse dans bCNC, si il y en qu'une il le décommente et j'ai des erreurs.
                                        
                    comment=comment_layer + comment_path
                    
                    #ici je definie un set d'outils en fonction du calque ou je me trouve.
                    #inkex.errormsg(inkex.Color(stroke).to_rgba())


                    Ok=False
                    couleur=inkex.Color(stroke).to_rgba()
                   # inkex.errormsg(couleur[0])
                    #defnition de l'outils pour la gravure laser, version par défaut dans un dict
                    if self.options.power_delay < 0.1:
                        Pause=""
                    else:
                        Pause="\nG4 P{}".format(round(self.options.power_delay,1))



                    if canal_pur(couleur, COLOR_CHANNEL_GRAV):  # canal de gravure seul au dessus du seuil, je grave
                        self.tools = {
                        "name": "Laser Engraver",
                        "id": "Laser Engraver",
                        "penetration feed": int(self.options.grav_laser_speed),
                        # >>> CORRECTION 7 : feed toujours entier (avant : round(...,0) renvoyait un float -> F750.0)
                        "feed": int(round(int(self.options.grav_laser_speed)*self.pc_couleur(couleur[COLOR_CHANNEL_GRAV]))),
                        # <<< FIN CORRECTION 7
                        "gcode before path": self.options.laser_on_command_grav + " S" + str(round(int(self.options.grav_laser_power)*stroke_opacity,2)) + Pause,
                        "gcode after path": self.options.laser_off_command + " S0" + "\n" + "G0 F" + self.options.travel_speed,
                        "Pass_in":1,
                        "Pass_depth":0,
                        "Z_start": self.options.grav_Z,
                        }
                        Ok=True
                    elif canal_pur(couleur, COLOR_CHANNEL_CUT): #sinon je regarde le canal de découpe, idem
                        self.tools = {
                        "name": "Laser cutter",
                        "id": "Laser cutter",
                        "penetration feed": int(self.options.cut_laser_speed),
                        # >>> CORRECTION 7 : feed toujours entier, meme calcul que la gravure (avant : int() puis round())
                        "feed": int(round(int(self.options.cut_laser_speed)*self.pc_couleur(couleur[COLOR_CHANNEL_CUT]))),
                        # <<< FIN CORRECTION 7
                        "gcode before path":  self.options.laser_on_command_cut + " S" + str(round(int(self.options.cut_laser_power)*stroke_opacity,2)) + Pause ,
                        "gcode after path": self.options.laser_off_command + " S0" + "\n" + "G0 F" + self.options.travel_speed ,
                        "Pass_in":self.options.cut_passes,
                        "Pass_depth":self.options.cut_pass_depth,
                        "Z_start": self.options.cut_Z,
                        }
                        Ok=True

                    #inkex.errormsg(self.tools)
                    #gestion des chemin qui sont rendue invisible  ou avec la couleur verte
                    if Ok and display=='inline':
                        curves += [
                            [
                                [id_, self.tools, comment],
                                [self.parse_curve([subpath], layer) for subpath in csp] #ceci découpe les chemins fait en plusieur partie de courbe simple
                            ]
                        ]
                        comment_layer= ""  #je reinitialise le commentaire du calque/group une fois au moins un chemin a été pris en compte


                #maintenant que les chemin sont répertorier je les dessine
                for curve in curves:
                    for subcurve in curve[1]:
                        self.draw_curve(subcurve, layer, PreviewGroups,name=curve[0][0])

                #passage en ordonnancement direct
                # >>> EVOLUTION ordonnancement : dans un même calque/groupe la gravure passe avant la découpe
                # (le tri par proximité se fait séparément pour chaque outil, résultat inchangé si le calque n'a qu'un seul outil)
                keys = []
                for nom_outil in ("Laser Engraver", "Laser cutter"):
                    indices = [i for i in range(len(curves)) if curves[i][0][1]["name"] == nom_outil]
                    keys += [indices[k] for k in sort_curves([curves[i][1] for i in indices])]
                # <<< FIN EVOLUTION ordonnancement
                for key in keys:
                    #attention ici on est sur un ensemble avec une profondeur de passe
                    path_tool=curves[key][0][1] #je récupère les infos d'outils spécifique a la courbe
                    for step in range(0, int(path_tool["Pass_in"])):
                        z =  path_tool["Z_start"] -(path_tool["Pass_depth"] * (step))
                        if curves[key][0][2] != "()" and step ==0:
                            gcode += curves[key][0][2]  # add comment

                        for curve in curves[key][1]:
                            gcode += self.generate_gcode(path_tool,curve, layer, z)
 
            
        self.export_gcode(gcode)

################################################################################
#
# conversion couleur en poucentage
#
################################################################################
    def pc_couleur(self,couleur):
        # >>> CORRECTION 3 : courbe monotone, mini 10% (avant : 105 donnait 5%, 108 donnait 8%, puis 110 redonnait 10%)
        if couleur > 200:
            return 1
        return max(.1, (couleur-100)/100) # mini a 10% de la vitesse pour éviter que cela ne bouge plus
        # <<< FIN CORRECTION 3

################################################################################
#
# Generate Gcode
# Generates Gcode on given curve.
#
# Curve definition [start point, type = {'arc','line','move','end'}, arc center, arc angle, end point, [zstart, zend]]
#
################################################################################
    def generate_gcode(self, path_tool,curve, layer, depth):
        tool = path_tool
        g = ""
        
        def c(c):
            c = [c[i] if i < len(c) else None for i in range(6)]
            if c[5] == 0:
                c[5] = None
            s = [" X", " Y", " Z", " I", " J", " K"]
            s1 = ["", "", "", "", "", ""]
            m = [1, 1, 1, 1, 1, 1]
            a = [0, 0, 0.0, 0, 0, 0]
            r = ''
            for i in range(6):
                if c[i] is not None:
                    r += s[i] + ("{:f}".format(c[i] * m[i] + a[i])) + s1[i]
            return r

        if len(curve) == 0:
            return ""

        lg = 'G00'
        f = " F{}".format(tool['feed'])
        for i in range(1, len(curve)):
            #    Creating Gcode for curve between s=curve[i-1] and si=curve[i] start at s[0] end at s[4]=si[0]
            s = curve[i - 1]
            si = curve[i]
            feed = f if lg not in ['G01', 'G02', 'G03'] else ''
            if s[1] == 'move':
                g += "G00" + c(si[0]+[depth]) + "\n" + tool['gcode before path'] + "\n"
                lg = 'G00'
            elif s[1] == 'end':
                g += tool['gcode after path'] + "\n"
                lg = 'G00'
            elif s[1] == 'line':
                g += "G01" + c(si[0] ) + feed + "\n"
                lg = 'G01'
            elif s[1] == 'arc':
                r = [(s[2][0] - s[0][0]), (s[2][1] - s[0][1])]
                if (r[0] ** 2 + r[1] ** 2) > self.options.min_arc_radius ** 2:
                    r1 = (P(s[0]) - P(s[2]))
                    r2 = (P(si[0]) - P(s[2]))
                    if abs(r1.mag() - r2.mag()) < 0.001:
                        g += ("G02" if s[3] < 0 else "G03") + c(si[0] + [s[5][1] + depth, (s[2][0] - s[0][0]), (s[2][1] - s[0][1])]) + feed + "\n"
                    else:
                        r = (r1.mag() + r2.mag()) / 2
                        g += ("G02" if s[3] < 0 else "G03") + c(si[0] + [s[5][1] + depth]) + " R{:f}".format(r) + feed + "\n"
                    lg = 'G02'
                else:
                    g += "G00" + c(si[0] + [s[5][1] + depth]) + feed + "\n"
                    lg = 'G00'
        if si[1] == 'end':
            g += tool['gcode after path'] + "\n"
        return g

################################################################################
###        Errors handling function, notes are just printed into Logfile, 
###        warnings are printed into log file and warning message is displayed but
###        extension continues working, errors causes log and execution is halted
###        Notes, warnings adn errors could be assigned to space or comma or dot 
###        sepparated strings (case is ignoreg).
################################################################################
    def error(self, s, type_= "Warning"):
        errors = """
                        Error     
                        wrong_orientation_points    
                        area_tools_diameter_error
                        no_tool_error
                        active_layer_already_has_tool
                        active_layer_already_has_orientation_points
                    """
        s = str(s)
        #version simplifier sans le log, si c'est pas une erreur on met juste un message d'info, sinon j'interompt le process
        if type_.lower() in re.split("[\n]+", errors.lower()) :
            inkex.errormsg(s+"\n")        
            sys.exit()
        else :
            inkex.errormsg(s)        

################################################################################
###         
###        Zone Get_transform reverse transform et apply_transform
################################################################################
    def get_transforms(self, g):
        root = self.document.getroot()
        trans = []
        while g != root:
            if 'transform' in g.keys():
                t = g.get('transform')
                t = Transform(t).matrix
                trans = (Transform(t) @ Transform(trans)).matrix if trans != [] else t

            g = g.getparent()
        return trans

    def reverse_transform(self, transform):
        trans = numpy.array(transform + ([0, 0, 1],))
        if numpy.linalg.det(trans) != 0:
            trans = numpy.linalg.inv(trans).tolist()[:2]
            return trans
        else:
            return transform

    def apply_transforms(self, g, csp, reverse=False):
        trans = self.get_transforms(g)
        if trans:
            if not reverse:
                for comp in csp:
                    for ctl in comp:
                        for pt in ctl:
                            pt[0], pt[1] = Transform(trans).apply_to_point(pt)

            else:
                for comp in csp:
                    for ctl in comp:
                        for pt in ctl:
                            pt[0], pt[1] = Transform(self.reverse_transform(trans)).apply_to_point(pt)
        return csp

    def transform(self, source_point, layer, reverse=False):
        if layer not in self.transform_matrix:
            for i in range(self.layers.index(layer), -1, -1):
                if self.layers[i] in self.orientation_points:
                    break
            if self.layers[i] not in self.orientation_points:
                self.error("Orientation points have not been found!", "error")
            elif self.layers[i] in self.transform_matrix:
                self.transform_matrix[layer] = self.transform_matrix[self.layers[i]]
                self.Zcoordinates[layer] = self.Zcoordinates[self.layers[i]]
            else:
                orientation_layer = self.layers[i]
                if len(self.orientation_points[orientation_layer]) > 1:
                    self.error(f"There are more than one orientation point groups in '{orientation_layer.label}' layer")
                points = self.orientation_points[orientation_layer][0]
                if len(points) == 2:
                    points += [[[(points[1][0][1] - points[0][0][1]) + points[0][0][0], -(points[1][0][0] - points[0][0][0]) + points[0][0][1]], [-(points[1][1][1] - points[0][1][1]) + points[0][1][0], points[1][1][0] - points[0][1][0] + points[0][1][1]]]]
                if len(points) == 3:

                    self.Zcoordinates[layer] = [max(points[0][1][2], points[1][1][2]), min(points[0][1][2], points[1][1][2])]
                    matrix = numpy.array([
                        [points[0][0][0], points[0][0][1], 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, points[0][0][0], points[0][0][1], 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, points[0][0][0], points[0][0][1], 1],
                        [points[1][0][0], points[1][0][1], 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, points[1][0][0], points[1][0][1], 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, points[1][0][0], points[1][0][1], 1],
                        [points[2][0][0], points[2][0][1], 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, points[2][0][0], points[2][0][1], 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, points[2][0][0], points[2][0][1], 1]
                    ])

                    if numpy.linalg.det(matrix) != 0:
                        m = numpy.linalg.solve(matrix,
                                               numpy.array(
                                                       [[points[0][1][0]], [points[0][1][1]], [1], [points[1][1][0]], [points[1][1][1]], [1], [points[2][1][0]], [points[2][1][1]], [1]]
                                               )
                                               ).tolist()
                        self.transform_matrix[layer] = [[m[j * 3 + i][0] for i in range(3)] for j in range(3)]

                    else:
                        self.error("Orientation points are wrong! (if there are two orientation points they should not be the same. If there are three orientation points they should not be in a straight line.)", "error")
                else:
                    self.error("Orientation points are wrong! (if there are two orientation points they should not be the same. If there are three orientation points they should not be in a straight line.)", "error")

            self.transform_matrix_reverse[layer] = numpy.linalg.inv(self.transform_matrix[layer]).tolist()

            self.Zauto_scale[layer] = 1

        x = source_point[0]
        y = source_point[1]
        if not reverse:
            t = self.transform_matrix[layer]
        else:
            t = self.transform_matrix_reverse[layer]
        return [t[0][0] * x + t[0][1] * y + t[0][2], t[1][0] * x + t[1][1] * y + t[1][2]]

    def transform_csp(self, csp_, layer, reverse=False):
        csp = [[[csp_[i][j][0][:], csp_[i][j][1][:], csp_[i][j][2][:]] for j in range(len(csp_[i]))] for i in range(len(csp_))]
        for i in range(len(csp)):
            for j in range(len(csp[i])):
                for k in range(len(csp[i][j])):
                    csp[i][j][k] = self.transform(csp[i][j][k], layer, reverse)
        return csp

        
###############################################################################
###
###        Get Gcodetools info from the svg
###
################################################################################
    def get_info(self):
        """Get Gcodetools info from the svg"""
        self.selected_paths = {}
        self.paths = {}
        self.tools = {}
        self.orientation_points = {}
        self.layers = [self.document.getroot()]
        self.Zcoordinates = {}
        self.transform_matrix = {}
        self.transform_matrix_reverse = {}
        self.Zauto_scale = {}
        self.DocName=""
              
        def recursive_search(g, layer, selected=False,level=""):

            items = g.getchildren()
            items.reverse()
            for i in items:
                if selected:
                    self.svg.selected[i.get("id")] = i

                if i.get(self.Zone_name['Definition']) == "Orientation group":
                    points = self.get_orientation_points(i)

                    if points is not None:
                        self.orientation_points[layer] = self.orientation_points[layer] + [points[:]] if layer in self.orientation_points else [points[:]]
                    else:
                        self.error(f"Warning! Found bad orientation points in '{layer.label}' layer. Resulting Gcode could be corrupt!")
                elif isinstance(i, inkex.Group) or isinstance(i, Layer):
                    invisible=i.style('display')
                    if invisible=='inline':
                        self.layers += [i]
                        recursive_search(i, i, (i.get("id") in self.svg.selected))#la partie selected permet de concerver le récursif sur le group
                        
                elif isinstance(i, inkex.PathElement):
                    if self.Zone_name['Definition'] not in i.keys():
                        self.paths[layer] = self.paths[layer] + [i] if layer in self.paths else [i]

                        if i.get("id") in self.svg.selected.ids:
                            self.selected_paths[layer] = self.selected_paths[layer] + [i] if layer in self.selected_paths else [i]
        
                elif i.get("id") in self.svg.selected:
                    # xgettext:no-pango-format
                    if i.label != None:
                        objet=i.label
                    else:
                        objet=i.get("id")
                        
                    self.error("This extension works with Paths and Dynamic Offsets and groups of them only! "
                               "All other objects will be ignored!\n"
                               "Solution 1: press Path->Object to path or Shift+Ctrl+C.\n"
                               "Solution 2: Path->Dynamic offset or Ctrl+J.\n"
                               "Solution 3: export all contours to PostScript level 2 (File->Save As->.ps) and File->Import this file.\n{}".format(objet))
    
        recursive_search(self.document.getroot(), self.document.getroot())
    
        if len(self.layers) == 1:
            self.error("Document has no layers! Add at least one layer using layers panel (Ctrl+Shift+L)", "error")
        root = self.document.getroot()
    
        #récupération du nom
        self.DocName=root.get("sodipodi:docname")
        
        if root in self.selected_paths or root in self.paths:
            self.error("Warning! There are some paths in the root of the document, but not in any layer! Using bottom-most layer for them.")
    
        if root in self.selected_paths:
            if self.layers[-1] in self.selected_paths:
                self.selected_paths[self.layers[-1]] += self.selected_paths[root][:]
            else:
                self.selected_paths[self.layers[-1]] = self.selected_paths[root][:]
            del self.selected_paths[root]
    
        if root in self.paths:
            if self.layers[-1] in self.paths:
                self.paths[self.layers[-1]] += self.paths[root][:]
            else:
                self.paths[self.layers[-1]] = self.paths[root][:]
            del self.paths[root]
    
    def get_orientation_points(self, g):
        items = g.getchildren()
        items.reverse()
        p2 = []
        p = None
        for i in items:
            if isinstance(i, inkex.Group):
                p2 += [i]
        p = p2
        if p is None:
            return None
        points = []
        for i in p:
            point = [[], []]
            for node in i:
                if node.get(self.Zone_name['Definition']) == "Orientation point arrow":
                    csp = node.path.transform(node.composed_transform()).to_superpath()
                    point[0] = csp[0][0][1]
                if node.get(self.Zone_name['Definition']) == "Orientation point text":
                    r = re.match(r'(?i)\s*\(\s*(-?\s*\d*(?:,|\.)*\d*)\s*;\s*(-?\s*\d*(?:,|\.)*\d*)\s*;\s*(-?\s*\d*(?:,|\.)*\d*)\s*\)\s*', node.get_text())
                    point[1] = [float(r.group(1)), float(r.group(2)), float(r.group(3))]
            if point[0] != [] and point[1] != []:
                points += [point]
        if len(points) == len(p2) == 2 :
            return points
        else:
            return None


################################################################################
###
###        Orientation
###
################################################################################
    def orientation(self, layer=None):
        if layer is None:
            layer = self.svg.get_current_layer() if self.svg.get_current_layer() is not None else self.document.getroot()

        transform = self.get_transforms(layer)
        if transform:
            transform = self.reverse_transform(transform)
            transform = str(Transform(transform))

        if layer in self.orientation_points:
            None
            #"Active layer already has orientation points! Remove them or select another layer!", "error")
        else:
            attr = {self.Zone_name['Definition']: "Orientation group"}
            
            if transform:
                attr["transform"] = transform
    
            orientation_group = layer.add(Group(**attr))
            orientation_group.label="Orientation group"
            doc_height = self.svg.unittouu(self.document.getroot().get('height'))
            if self.document.getroot().get('height') == "100%":
                doc_height = 1052.3622047
            if self.options.unit == "G21 (All units in mm)":
                points = [[0., 0., 0.], [100., 0., 0.], [0., 100., 0.]]
            elif self.options.unit == "G20 (All units in inches)":
                points = [[0., 0., 0.], [5., 0., 0.], [0., 5., 0.]]
            points = points[:2]
            for i in points:
                name = {self.Zone_name['Definition']:"Orientation point (2 points)"}
                grp = orientation_group.add(Group(**name))
                grp.label="({}; {}; {})".format(i[0], i[1], i[2])
                elem = grp.add(PathElement(style="stroke:none;fill:#000000;"))
                elem.set(self.Zone_name['Definition'], "Orientation point arrow")
                elem.path = 'm {},{} 2.9375,-6.343750000001 0.8125,1.90625 6.843748640396,'\
                    '-6.84374864039 0,0 0.6875,0.6875 -6.84375,6.84375 1.90625,0.812500000'\
                    '001 z'.format(i[0], -i[1] + doc_height)
                elem.label="Orientation points arrow"
                draw_text("({}; {}; {})".format(i[0], i[1], i[2]), (i[0] + 10), (-i[1] - 10 + doc_height), group=grp, gcodetools_tag="Orientation point text",label_text="Orientation point text")


################################################################################
###
###       Export_gcode
###
###        Main function of Gcodetools class
###
################################################################################
    def check_dir(self):
        if os.path.isdir(self.options.directory):
            if os.path.isfile(os.path.join(self.options.directory, 'header')):
                with open(os.path.join(self.options.directory, 'header')) as f:
                    self.header = f.read()
            else:
                self.header ="\n(GCODE realiser avec l'extension inskape Path2Laser_GCODE de madeinfonddugarage)\n{}\n".format(self.options.Gcode_start).replace("\\n","\n")
            if os.path.isfile(os.path.join(self.options.directory, 'footer')):
                with open(os.path.join(self.options.directory, 'footer')) as f:
                    self.footer = f.read()
            else:
                self.footer = self.options.Gcode_end.replace("\\n","\n")
            self.header += self.options.unit + "\n"
        else:
            self.error("Directory does not exist! Please specify existing directory at Preferences tab!", "error")
            return False
    
        if self.options.add_numeric_suffix_to_filename:
            dir_list = os.listdir(self.options.directory)
            if "." in self.options.file:
                r = re.match(r"^(.*)(\..*)$", self.options.file)
                ext = r.group(2)
                name = r.group(1)
            else:
                ext = ""
                name = self.options.file
            max_n = 0
            for s in dir_list:
                r = re.match(r"^{}_0*(\d+){}$".format(re.escape(name), re.escape(ext)), s)
                if r:
                    max_n = max(max_n, int(r.group(1)))
            filename = name + "_" + ("0" * (4 - len(str(max_n + 1))) + str(max_n + 1)) + ext
            self.options.file = filename
    
        try:
            with open(os.path.join(self.options.directory, self.options.file), "w") as f:
                pass
        except:
            self.error("Can not write to specified file!\n{}".format(os.path.join(self.options.directory, self.options.file)), "error")
            return False
        return True              

    def parse_curve(self, p, layer, w=None, f=None):
        c = []
        if len(p) == 0:
            return []
        p = self.transform_csp(p, layer)

        for k in range(len(p)):
            subpath = p[k]
            c += [[[subpath[0][1][0], subpath[0][1][1]], 'move', 0, 0]]
            for i in range(1, len(subpath)):
                sp1 = [[subpath[i - 1][j][0], subpath[i - 1][j][1]] for j in range(3)]
                sp2 = [[subpath[i][j][0], subpath[i][j][1]] for j in range(3)]
                c += biarc(sp1, sp2, 0, 0) if w is None else biarc(sp1, sp2, -f(w[k][i - 1]), -f(w[k][i]))
            c += [[[subpath[-1][1][0], subpath[-1][1][1]], 'end', 0, 0]]
        return c
       
    def export_gcode(self,gcode):
        #export du gcode un fois finie
        # >>> CORRECTION 1 : os.path.join (avant : directory+file, faux sans "/" final, le fichier partait à côté du dossier)
        f = open(os.path.join(self.options.directory, self.options.file), "w")
        # <<< FIN CORRECTION 1
        if self.DocName==None:
            NomDessin="Iconnu"
        else:
            NomDessin=self.DocName
        f.write( "(Block-name:Start)\n\n(Gcode creer a partir du fichier %s) %s%s S0 \nG0 F%s\n%s \n(Block-name:End)\n%s" %(NomDessin,self.header,self.options.laser_off_command ,self.options.travel_speed,gcode,self.footer))
        f.close()


################################################################################
#
# draw csp
#
################################################################################
    def draw_curve(self, curve, layer, groupbase=None, style=MARKER_STYLE["biarc_style"],name=""):
        
        attr={self.Zone_name['Definition']:'Preview group'}
        group= groupbase.add(Group(**attr))
        group.label='Preview de {}'.format(name)
            
        s = ''
        arcn = 0

        transform = self.get_transforms(group)
        if transform:
            transform = self.reverse_transform(transform)
            transform = str(Transform(transform))

        a = [0., 0.]
        b = [1., 0.]
        c = [0., 1.]
        k = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        a = self.transform(a, layer, True)
        b = self.transform(b, layer, True)
        c = self.transform(c, layer, True)
        if ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) * k > 0:
            reverse_angle = 1
        else:
            reverse_angle = -1

        for sk in curve:
            si = sk[:] #sk contient les movement et les position relative
            si[0] = self.transform(si[0], layer, True)
            si[2] = self.transform(si[2], layer, True) if type(si[2]) == type([]) and len(si[2]) == 2 else si[2]

            if s != '':
                if s[1] == 'line':
                    attr={self.Zone_name['Definition']:'Preview line'}
                    elem = group.add(PathElement(**attr))
                    elem.label='Preview line {}'.format(name)
                    elem.transform = transform
                    elem.style = style['line']
                    elem.path = 'M {},{} L {},{}'.format(s[0][0], s[0][1], si[0][0], si[0][1])
                elif s[1] == 'arc':
                    arcn += 1
                    sp = s[0]
                    c = s[2]
                    s[3] = s[3] * reverse_angle

                    a = ((P(si[0]) - P(c)).angle() - (P(s[0]) - P(c)).angle()) % TAU  # s[3]
                    if s[3] * a < 0:
                        if a > 0:
                            a = a - TAU
                        else:
                            a = TAU + a
                    r = math.sqrt((sp[0] - c[0]) ** 2 + (sp[1] - c[1]) ** 2)
                    a_st = (math.atan2(sp[0] - c[0], - (sp[1] - c[1])) - math.pi / 2) % (math.pi * 2)
                    if a > 0:
                        a_end = a_st + a
                        st = style['biarc{}'.format(arcn % 2)]
                    else:
                        a_end = a_st * 1
                        a_st = a_st + a
                        st = style['biarc{}'.format(arcn % 2)]
                    attr={self.Zone_name['Definition']:'Preview arc'}
                    elem = group.add(PathElement.arc(c, r, start=a_st, end=a_end,
                                                     open=True, **attr))
                    elem.label='Preview arc {}'.format(name)
                    elem.transform = transform
                    elem.style = st

            s = si

################################################################################
#
# Type d'un chemin pour l'ordonnancement : "grav", "cut" ou None
# None si le chemin est invisible, sans "d" ou de couleur non reconnue (mêmes règles que path_to_gcode)
#
################################################################################
def type_chemin(chemin):
    if "d" not in chemin.keys() or chemin.style('display') != 'inline':
        return None
    couleur = inkex.Color(chemin.style('stroke')).to_rgba()
    if canal_pur(couleur, COLOR_CHANNEL_GRAV):
        return "grav"
    if canal_pur(couleur, COLOR_CHANNEL_CUT):
        return "cut"
    return None

################################################################################
#
# Test de couleur : le canal choisi seul est au dessus du seuil
# couleur = to_rgba() ; renvoie False pour une couleur mélangée, noire ou sans couleur
#
################################################################################
def canal_pur(couleur, canal):
    if couleur[canal] < COLOR_SEUIL:
        return False
    for i in range(3):
        if i != canal and couleur[i] >= COLOR_SEUIL:
            return False
    return True

################################################################################
#
# Biarc function
#
# Calculates biarc approximation of cubic super path segment
#  splits segment if needed or approximates it with straight line
#
################################################################################
def biarc(sp1, sp2, z1, z2, depth=0):
    def biarc_split(sp1, sp2, z1, z2, depth):
        if depth < options.biarc_max_split_depth:
            sp1, sp2, sp3 = csp_split(sp1, sp2)
            l1 = cspseglength(sp1, sp2)
            l2 = cspseglength(sp2, sp3)
            if l1 + l2 == 0:
                zm = z1
            else:
                zm = z1 + (z2 - z1) * l1 / (l1 + l2)
            return biarc(sp1, sp2, z1, zm, depth + 1) + biarc(sp2, sp3, zm, z2, depth + 1)
        else:
            return [[sp1[1], 'line', 0, 0, sp2[1], [z1, z2]]]

    P0 = P(sp1[1])
    P4 = P(sp2[1])
    TS = (P(sp1[2]) - P0)
    TE = -(P(sp2[0]) - P4)
    v = P0 - P4
    tsa = TS.angle()
    tea = TE.angle()
    if TE.mag() < STRAIGHT_DISTANCE_TOLERANCE and TS.mag() < STRAIGHT_DISTANCE_TOLERANCE:
        # Both tangents are zero - line straight
        return [[sp1[1], 'line', 0, 0, sp2[1], [z1, z2]]]
    if TE.mag() < STRAIGHT_DISTANCE_TOLERANCE:
        TE = -(TS + v).unit()
        r = TS.mag() / v.mag() * 2
    elif TS.mag() < STRAIGHT_DISTANCE_TOLERANCE:
        TS = -(TE + v).unit()
        r = 1 / (TE.mag() / v.mag() * 2)
    else:
        r = TS.mag() / TE.mag()
    TS = TS.unit()
    TE = TE.unit()
    tang_are_parallel = ((tsa - tea) % math.pi < STRAIGHT_TOLERANCE or math.pi - (tsa - tea) % math.pi < STRAIGHT_TOLERANCE)
    if (tang_are_parallel and
            ((v.mag() < STRAIGHT_DISTANCE_TOLERANCE or TE.mag() < STRAIGHT_DISTANCE_TOLERANCE or TS.mag() < STRAIGHT_DISTANCE_TOLERANCE) or
             1 - abs(TS * v / (TS.mag() * v.mag())) < STRAIGHT_TOLERANCE)):
        # Both tangents are parallel and start and end are the same - line straight
        # or one of tangents still smaller then tolerance

        # Both tangents and v are parallel - line straight
        return [[sp1[1], 'line', 0, 0, sp2[1], [z1, z2]]]

    c = v * v
    b = 2 * v * (r * TS + TE)
    a = 2 * r * (TS * TE - 1)
    if v.mag() == 0:
        return biarc_split(sp1, sp2, z1, z2, depth)
    asmall = abs(a) < 10 ** -10
    bsmall = abs(b) < 10 ** -10
    csmall = abs(c) < 10 ** -10
    if asmall and b != 0:
        beta = -c / b
    elif csmall and a != 0:
        beta = -b / a
    elif not asmall:
        discr = b * b - 4 * a * c
        if discr < 0:
            raise ValueError(a, b, c, discr)
        disq = discr ** .5
        beta1 = (-b - disq) / 2 / a
        beta2 = (-b + disq) / 2 / a
        if beta1 * beta2 > 0:
            raise ValueError(a, b, c, disq, beta1, beta2)
        beta = max(beta1, beta2)
    elif asmall and bsmall:
        return biarc_split(sp1, sp2, z1, z2, depth)
    alpha = beta * r
    ab = alpha + beta
    P1 = P0 + alpha * TS
    P3 = P4 - beta * TE
    P2 = (beta / ab) * P1 + (alpha / ab) * P3

    def calculate_arc_params(P0, P1, P2):
        D = (P0 + P2) / 2
        if (D - P1).mag() == 0:
            return None, None
        R = D - ((D - P0).mag() ** 2 / (D - P1).mag()) * (P1 - D).unit()
        p0a = (P0 - R).angle() % (2 * math.pi)
        p1a = (P1 - R).angle() % (2 * math.pi)
        p2a = (P2 - R).angle() % (2 * math.pi)
        alpha = (p2a - p0a) % (2 * math.pi)
        if (p0a < p2a and (p1a < p0a or p2a < p1a)) or (p2a < p1a < p0a):
            alpha = -2 * math.pi + alpha
        if abs(R.x) > 1000000 or abs(R.y) > 1000000 or (R - P0).mag() < options.min_arc_radius ** 2:
            return None, None
        else:
            return R, alpha

    R1, a1 = calculate_arc_params(P0, P1, P2)
    R2, a2 = calculate_arc_params(P2, P3, P4)
    if R1 is None or R2 is None or (R1 - P0).mag() < STRAIGHT_TOLERANCE or (R2 - P2).mag() < STRAIGHT_TOLERANCE:
        return [[sp1[1], 'line', 0, 0, sp2[1], [z1, z2]]]

    d = csp_to_arc_distance(sp1, sp2, [P0, P2, R1, a1], [P2, P4, R2, a2])
    if d > options.biarc_tolerance and depth < options.biarc_max_split_depth:
        return biarc_split(sp1, sp2, z1, z2, depth)
    else:
        if R2.mag() * a2 == 0:
            zm = z2
        else:
            zm = z1 + (z2 - z1) * (abs(R1.mag() * a1)) / (abs(R2.mag() * a2) + abs(R1.mag() * a1))

        l = (P0 - P2).l2()
        if l < EMC_TOLERANCE_EQUAL ** 2 or l < EMC_TOLERANCE_EQUAL ** 2 * R1.l2() / 100:
            # arc should be straight otherwise it could be treated as full circle
            arc1 = [sp1[1], 'line', 0, 0, [P2.x, P2.y], [z1, zm]]
        else:
            arc1 = [sp1[1], 'arc', [R1.x, R1.y], a1, [P2.x, P2.y], [z1, zm]]

        l = (P4 - P2).l2()
        if l < EMC_TOLERANCE_EQUAL ** 2 or l < EMC_TOLERANCE_EQUAL ** 2 * R2.l2() / 100:
            # arc should be straight otherwise it could be treated as full circle
            arc2 = [[P2.x, P2.y], 'line', 0, 0, [P4.x, P4.y], [zm, z2]]
        else:
            arc2 = [[P2.x, P2.y], 'arc', [R2.x, R2.y], a2, [P4.x, P4.y], [zm, z2]]

        return [arc1, arc2]
    

################################################################################
# Cubic Super Path additional functions
################################################################################

def csp_segment_to_bez(sp1, sp2):
    return sp1[1:] + sp2[:2]


def csp_split(sp1, sp2, t=.5):
    [x1, y1] = sp1[1]
    [x2, y2] = sp1[2]
    [x3, y3] = sp2[0]
    [x4, y4] = sp2[1]
    x12 = x1 + (x2 - x1) * t
    y12 = y1 + (y2 - y1) * t
    x23 = x2 + (x3 - x2) * t
    y23 = y2 + (y3 - y2) * t
    x34 = x3 + (x4 - x3) * t
    y34 = y3 + (y4 - y3) * t
    x1223 = x12 + (x23 - x12) * t
    y1223 = y12 + (y23 - y12) * t
    x2334 = x23 + (x34 - x23) * t
    y2334 = y23 + (y34 - y23) * t
    x = x1223 + (x2334 - x1223) * t
    y = y1223 + (y2334 - y1223) * t
    return [sp1[0], sp1[1], [x12, y12]], [[x1223, y1223], [x, y], [x2334, y2334]], [[x34, y34], sp2[1], sp2[2]]



############################################################################
# csp_segments_intersection(sp1,sp2,sp3,sp4)
#
# Returns array containing all intersections between two segments of cubic
# super path. Results are [ta,tb], or [ta0, ta1, tb0, tb1, "Overlap"]
# where ta, tb are values of t for the intersection point.
############################################################################
def csp_segments_intersection(sp1, sp2, sp3, sp4):
    a = csp_segment_to_bez(sp1, sp2)
    b = csp_segment_to_bez(sp3, sp4)

    def polish_intersection(a, b, ta, tb, tolerance=INTERSECTION_TOLERANCE):
        ax, ay, bx, by, cx, cy, dx, dy = bezierparameterize(a)
        ax1, ay1, bx1, by1, cx1, cy1, dx1, dy1 = bezierparameterize(b)
        i = 0
        F = [.0, .0]
        F1 = [[.0, .0], [.0, .0]]
        while i == 0 or (abs(F[0]) ** 2 + abs(F[1]) ** 2 > tolerance and i < 10):
            ta3 = ta ** 3
            ta2 = ta ** 2
            tb3 = tb ** 3
            tb2 = tb ** 2
            F[0] = ax * ta3 + bx * ta2 + cx * ta + dx - ax1 * tb3 - bx1 * tb2 - cx1 * tb - dx1
            F[1] = ay * ta3 + by * ta2 + cy * ta + dy - ay1 * tb3 - by1 * tb2 - cy1 * tb - dy1
            F1[0][0] = 3 * ax * ta2 + 2 * bx * ta + cx
            F1[0][1] = -3 * ax1 * tb2 - 2 * bx1 * tb - cx1
            F1[1][0] = 3 * ay * ta2 + 2 * by * ta + cy
            F1[1][1] = -3 * ay1 * tb2 - 2 * by1 * tb - cy1
            det = F1[0][0] * F1[1][1] - F1[0][1] * F1[1][0]
            if det != 0:
                F1 = [[F1[1][1] / det, -F1[0][1] / det], [-F1[1][0] / det, F1[0][0] / det]]
                ta = ta - (F1[0][0] * F[0] + F1[0][1] * F[1])
                tb = tb - (F1[1][0] * F[0] + F1[1][1] * F[1])
            else:
                break
            i += 1

        return ta, tb

    def recursion(a, b, ta0, ta1, tb0, tb1, depth_a, depth_b):
        global bezier_intersection_recursive_result
        if a == b:
            bezier_intersection_recursive_result += [[ta0, tb0, ta1, tb1, "Overlap"]]
            return
        tam = (ta0 + ta1) / 2
        tbm = (tb0 + tb1) / 2
        if depth_a > 0 and depth_b > 0:
            a1, a2 = bez_split(a, 0.5)
            b1, b2 = bez_split(b, 0.5)
            if bez_bounds_intersect(a1, b1):
                recursion(a1, b1, ta0, tam, tb0, tbm, depth_a - 1, depth_b - 1)
            if bez_bounds_intersect(a2, b1):
                recursion(a2, b1, tam, ta1, tb0, tbm, depth_a - 1, depth_b - 1)
            if bez_bounds_intersect(a1, b2):
                recursion(a1, b2, ta0, tam, tbm, tb1, depth_a - 1, depth_b - 1)
            if bez_bounds_intersect(a2, b2):
                recursion(a2, b2, tam, ta1, tbm, tb1, depth_a - 1, depth_b - 1)
        elif depth_a > 0:
            a1, a2 = bez_split(a, 0.5)
            if bez_bounds_intersect(a1, b):
                recursion(a1, b, ta0, tam, tb0, tb1, depth_a - 1, depth_b)
            if bez_bounds_intersect(a2, b):
                recursion(a2, b, tam, ta1, tb0, tb1, depth_a - 1, depth_b)
        elif depth_b > 0:
            b1, b2 = bez_split(b, 0.5)
            if bez_bounds_intersect(a, b1):
                recursion(a, b1, ta0, ta1, tb0, tbm, depth_a, depth_b - 1)
            if bez_bounds_intersect(a, b2):
                recursion(a, b2, ta0, ta1, tbm, tb1, depth_a, depth_b - 1)
        else:  # Both segments have been subdivided enough. Let's get some intersections :).
            intersection, t1, t2 = straight_segments_intersection([a[0]] + [a[3]], [b[0]] + [b[3]])
            if intersection:
                if intersection == "Overlap":
                    t1 = (max(0, min(1, t1[0])) + max(0, min(1, t1[1]))) / 2
                    t2 = (max(0, min(1, t2[0])) + max(0, min(1, t2[1]))) / 2
                bezier_intersection_recursive_result += [[ta0 + t1 * (ta1 - ta0), tb0 + t2 * (tb1 - tb0)]]

    global bezier_intersection_recursive_result
    bezier_intersection_recursive_result = []
    recursion(a, b, 0., 1., 0., 1., INTERSECTION_RECURSION_DEPTH, INTERSECTION_RECURSION_DEPTH)
    intersections = bezier_intersection_recursive_result
    for i in range(len(intersections)):
        if len(intersections[i]) < 5 or intersections[i][4] != "Overlap":
            intersections[i] = polish_intersection(a, b, intersections[i][0], intersections[i][1])
    return intersections


def csp_curvature_at_t(sp1, sp2, t, depth=3):
    ax, ay, bx, by, cx, cy, dx, dy = bezierparameterize(csp_segment_to_bez(sp1, sp2))

    # curvature = (x'y''-y'x'') / (x'^2+y'^2)^1.5

    f1x = 3 * ax * t ** 2 + 2 * bx * t + cx
    f1y = 3 * ay * t ** 2 + 2 * by * t + cy
    f2x = 6 * ax * t + 2 * bx
    f2y = 6 * ay * t + 2 * by
    d = (f1x ** 2 + f1y ** 2) ** 1.5
    if d != 0:
        return (f1x * f2y - f1y * f2x) / d
    else:
        t1 = f1x * f2y - f1y * f2x
        if t1 > 0:
            return 1e100
        if t1 < 0:
            return -1e100
        # Use the Lapitals rule to solve 0/0 problem for 2 times...
        t1 = 2 * (bx * ay - ax * by) * t + (ay * cx - ax * cy)
        if t1 > 0:
            return 1e100
        if t1 < 0:
            return -1e100
        t1 = bx * ay - ax * by
        if t1 > 0:
            return 1e100
        if t1 < 0:
            return -1e100
        if depth > 0:
            # little hack ;^) hope it won't influence anything...
            return csp_curvature_at_t(sp1, sp2, t * 1.004, depth - 1)
        return 1e100



def csp_at_t(sp1, sp2, t):
    ax = sp1[1][0]
    bx = sp1[2][0]
    cx = sp2[0][0]
    dx = sp2[1][0]

    ay = sp1[1][1]
    by = sp1[2][1]
    cy = sp2[0][1]
    dy = sp2[1][1]

    x1 = ax + (bx - ax) * t
    y1 = ay + (by - ay) * t

    x2 = bx + (cx - bx) * t
    y2 = by + (cy - by) * t

    x3 = cx + (dx - cx) * t
    y3 = cy + (dy - cy) * t

    x4 = x1 + (x2 - x1) * t
    y4 = y1 + (y2 - y1) * t

    x5 = x2 + (x3 - x2) * t
    y5 = y2 + (y3 - y2) * t

    x = x4 + (x5 - x4) * t
    y = y4 + (y5 - y4) * t

    return [x, y]


def cspseglength(sp1, sp2, tolerance=0.01):
    bez = (sp1[1][:], sp1[2][:], sp2[0][:], sp2[1][:])
    return bezierlength(bez, tolerance)



def point_to_arc_distance(p, arc):
    # Distance calculattion from point to arc
    P0, P2, c, a = arc
    p = P(p)
    r = (P0 - c).mag()
    if r > 0:
        i = c + (p - c).unit() * r
        alpha = ((i - c).angle() - (P0 - c).angle())
        if a * alpha < 0:
            if alpha > 0:
                alpha = alpha - TAU
            else:
                alpha = TAU + alpha
        if between(alpha, 0, a) or min(abs(alpha), abs(alpha - a)) < STRAIGHT_TOLERANCE:
            return (p - i).mag(), [i.x, i.y]
        else:
            d1 = (p - P0).mag()
            d2 = (p - P2).mag()
            if d1 < d2:
                return d1, [P0.x, P0.y]
            else:
                return d2, [P2.x, P2.y]


def csp_to_arc_distance(sp1, sp2, arc1, arc2, tolerance=0.01):  # arc = [start,end,center,alpha]
    n = 10
    i = 0
    d = (0, [0, 0])
    d1 = (0, [0, 0])
    dl = 0
    while i < 1 or (abs(d1[0] - dl[0]) > tolerance and i < 4):
        i += 1
        dl = d1 * 1
        for j in range(n + 1):
            t = float(j) / n
            p = csp_at_t(sp1, sp2, t)
            d = min(point_to_arc_distance(p, arc1), point_to_arc_distance(p, arc2))
            d1 = max(d1, d)
        n = n * 2
    return d1[0]


def point_to_point_d2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def point_to_point_d(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def triangle_cross(a, b, c):
    return (a[0] - b[0]) * (c[1] - b[1]) - (c[0] - b[0]) * (a[1] - b[1])


def csp_segment_convex_hull(sp1, sp2):
    a = sp1[1][:]
    b = sp1[2][:]
    c = sp2[0][:]
    d = sp2[1][:]

    abc = triangle_cross(a, b, c)
    abd = triangle_cross(a, b, d)
    bcd = triangle_cross(b, c, d)
    cad = triangle_cross(c, a, d)
    if abc == 0 and abd == 0:
        return [min(a, b, c, d), max(a, b, c, d)]
    if abc == 0:
        return [d, min(a, b, c), max(a, b, c)]
    if abd == 0:
        return [c, min(a, b, d), max(a, b, d)]
    if bcd == 0:
        return [a, min(b, c, d), max(b, c, d)]
    if cad == 0:
        return [b, min(c, a, d), max(c, a, d)]

    m1 = abc * abd > 0
    m2 = abc * bcd > 0
    m3 = abc * cad > 0

    if m1 and m2 and m3:
        return [a, b, c]
    if m1 and m2 and not m3:
        return [a, b, c, d]
    if m1 and not m2 and m3:
        return [a, b, d, c]
    if not m1 and m2 and m3:
        return [a, d, b, c]
    if m1 and not (m2 and m3):
        return [a, b, d]
    if not (m1 and m2) and m3:
        return [c, a, d]
    if not (m1 and m3) and m2:
        return [b, c, d]

    raise ValueError("csp_segment_convex_hull happened which is something that shouldn't happen!")


################################################################################
# Bezier additional functions
################################################################################

def bez_bounds_intersect(bez1, bez2):
    return bounds_intersect(bez_bound(bez2), bez_bound(bez1))


def bez_bound(bez):
    return [
        min(bez[0][0], bez[1][0], bez[2][0], bez[3][0]),
        min(bez[0][1], bez[1][1], bez[2][1], bez[3][1]),
        max(bez[0][0], bez[1][0], bez[2][0], bez[3][0]),
        max(bez[0][1], bez[1][1], bez[2][1], bez[3][1]),
    ]


def bounds_intersect(a, b):
    return not ((a[0] > b[2]) or (b[0] > a[2]) or (a[1] > b[3]) or (b[1] > a[3]))


def tpoint(xy1, xy2, t):
    (x1, y1) = xy1
    (x2, y2) = xy2
    return [x1 + t * (x2 - x1), y1 + t * (y2 - y1)]


def bez_split(a, t=0.5):
    a1 = tpoint(a[0], a[1], t)
    at = tpoint(a[1], a[2], t)
    b2 = tpoint(a[2], a[3], t)
    a2 = tpoint(a1, at, t)
    b1 = tpoint(b2, at, t)
    a3 = tpoint(a2, b1, t)
    return [a[0], a1, a2, a3], [a3, b1, b2, a[3]]


################################################################################
# Some vector functions
################################################################################


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]



################################################################################
# Common functions
################################################################################



def atan2(*arg):
    if len(arg) == 1 and (type(arg[0]) == type([0., 0.]) or type(arg[0]) == type((0., 0.))):
        return (math.pi / 2 - math.atan2(arg[0][0], arg[0][1])) % TAU
    elif len(arg) == 2:
        return (math.pi / 2 - math.atan2(arg[0], arg[1])) % TAU
    else:
        raise ValueError("Bad argumets for atan! ({})".format(*arg))


def draw_text(text, x, y, group=None, style=None, font_size=10, gcodetools_tag=None,label_text=None):
    if style is None:
        style = "font-family:DejaVu Sans;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-family:DejaVu Sans;fill:#000000;fill-opacity:1;stroke:none;"
    style += "font-size:{:f}px;".format(font_size)
    attributes = {'x': str(x), 'y': str(y), 'style': style}
    if gcodetools_tag is not None:
        attributes[options.self.Zone_name['Definition']] = str(gcodetools_tag)

    if group is None:
        group = options.doc_root

    text_elem = group.add(TextElement(**attributes))
    if label_text != None:
        text_elem.label=label_text
    text_elem.set("xml:space", "preserve")
    text = str(text).split("\n")
    for string in text:
        span = text_elem.add(Tspan(x=str(x), y=str(y)))
        span.set('sodipodi:role', 'line')
        y += font_size
        span.text = str(string)



def straight_segments_intersection(a, b, true_intersection=True):  # (True intersection means check ta and tb are in [0,1])
    ax = a[0][0]
    bx = a[1][0]
    cx = b[0][0]
    dx = b[1][0]
    ay = a[0][1]
    by = a[1][1]
    cy = b[0][1]
    dy = b[1][1]
    if (ax == bx and ay == by) or (cx == dx and cy == dy):
        return False, 0, 0
    if (bx - ax) * (dy - cy) - (by - ay) * (dx - cx) == 0:  # Lines are parallel
        ta = (ax - cx) / (dx - cx) if cx != dx else (ay - cy) / (dy - cy)
        tb = (bx - cx) / (dx - cx) if cx != dx else (by - cy) / (dy - cy)
        tc = (cx - ax) / (bx - ax) if ax != bx else (cy - ay) / (by - ay)
        td = (dx - ax) / (bx - ax) if ax != bx else (dy - ay) / (by - ay)
        return ("Overlap" if 0 <= ta <= 1 or 0 <= tb <= 1 or 0 <= tc <= 1 or 0 <= td <= 1 or not true_intersection else False), (ta, tb), (tc, td)
    else:
        ta = ((ay - cy) * (dx - cx) - (ax - cx) * (dy - cy)) / ((bx - ax) * (dy - cy) - (by - ay) * (dx - cx))
        tb = (ax - cx + ta * (bx - ax)) / (dx - cx) if dx != cx else (ay - cy + ta * (by - ay)) / (dy - cy)
        return (0 <= ta <= 1 and 0 <= tb <= 1 or not true_intersection), ta, tb


def between(c, x, y):
    return x - STRAIGHT_TOLERANCE <= c <= y + STRAIGHT_TOLERANCE or y - STRAIGHT_TOLERANCE <= c <= x + STRAIGHT_TOLERANCE


#################################################################################
# Point (x,y) operations
################################################################################
class P(object):
    def __init__(self, x, y=None):
        if not y is None:
            self.x = float(x)
            self.y = float(y)
        else:
            self.x = float(x[0])
            self.y = float(x[1])

    def __add__(self, other):
        return P(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return P(self.x - other.x, self.y - other.y)

    def __neg__(self):
        return P(-self.x, -self.y)

    def __mul__(self, other):
        if isinstance(other, P):
            return self.x * other.x + self.y * other.y
        return P(self.x * other, self.y * other)

    __rmul__ = __mul__

    def __div__(self, other):
        return P(self.x / other, self.y / other)
 
    def __truediv__(self, other):
        return self.__div__(other)

    def mag(self):
        return math.hypot(self.x, self.y)

    def unit(self):
        h_mag = self.mag()
        if h_mag:
            return self / h_mag
        return P(0, 0)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def rot(self, theta):
        c = math.cos(theta)
        s = math.sin(theta)
        return P(self.x * c - self.y * s, self.x * s + self.y * c)

    def angle(self):
        return math.atan2(self.y, self.x)

    def __repr__(self):
        return '{:f},{:f}'.format(self.x, self.y)

    def pr(self):
        return "{:.2f},{:.2f}".format(self.x, self.y)

    def to_list(self):
        return [self.x, self.y] 

    def ccw(self):
        return P(-self.y, self.x)

    def l2(self):
        return self.x * self.x + self.y * self.y

#point de départ    
if __name__ == '__main__':
    Path2Laser().run()
    

