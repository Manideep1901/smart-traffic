import xml.etree.ElementTree as ET
import math
import random

# ==============================================================================
# GEOMETRY UTILITIES
# ==============================================================================

def parse_shape(shape_str):
    pts = []
    for pair in shape_str.strip().split():
        x, y = map(float, pair.split(','))
        pts.append((x, y))
    return pts

def format_shape(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

def point_in_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def dist_point_segment(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

def segments_intersect(p1, p2, p3, p4):
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))

def polygons_intersect(poly1, poly2):
    for x, y in poly1:
        if point_in_polygon(x, y, poly2):
            return True
    for x, y in poly2:
        if point_in_polygon(x, y, poly1):
            return True
    n1, n2 = len(poly1), len(poly2)
    for i in range(n1):
        e1_a, e1_b = poly1[i], poly1[(i + 1) % n1]
        for j in range(n2):
            e2_a, e2_b = poly2[j], poly2[(j + 1) % n2]
            if segments_intersect(e1_a, e1_b, e2_a, e2_b):
                return True
    return False

def make_rect(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

def make_l_shape(x1, y1, x2, y2, cut_w, cut_h, corner="top-right"):
    if corner == "top-right":
        return [
            (x1, y1), (x2, y1), (x2, y2 - cut_h),
            (x2 - cut_w, y2 - cut_h), (x2 - cut_w, y2), (x1, y2)
        ]
    elif corner == "top-left":
        return [
            (x1, y1), (x2, y1), (x2, y2),
            (x1 + cut_w, y2), (x1 + cut_w, y2 - cut_h), (x1, y2 - cut_h)
        ]
    elif corner == "bottom-right":
        return [
            (x1, y1 + cut_h), (x2 - cut_w, y1 + cut_h), (x2 - cut_w, y1),
            (x2, y1), (x2, y2), (x1, y2)
        ]
    else:
        return [
            (x1 + cut_w, y1), (x2, y1), (x2, y2),
            (x1, y2), (x1, y1 + cut_h), (x1 + cut_w, y1 + cut_h)
        ]

def make_u_shape(x1, y1, x2, y2, cutout_w, cutout_h):
    cw_half = cutout_w / 2.0
    cx = (x1 + x2) / 2.0
    return [
        (x1, y1), (x2, y1), (x2, y2),
        (cx + cw_half, y2), (cx + cw_half, y2 - cutout_h),
        (cx - cw_half, y2 - cutout_h), (cx - cw_half, y2),
        (x1, y2)
    ]

def make_rotated_rect(cx, cy, length, width, angle_deg):
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    hl = length / 2.0
    hw = width / 2.0
    corners = [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]
    rotated = []
    for dx, dy in corners:
        rx = cx + dx * cos_a - dy * sin_a
        ry = cy + dx * sin_a + dy * cos_a
        rotated.append((rx, ry))
    return rotated

def make_circle_poly(cx, cy, radius, num_pts=8):
    pts = []
    for i in range(num_pts):
        angle = 2 * math.pi * i / num_pts
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return pts

# ==============================================================================
# URBAN BUILDER CLASS
# ==============================================================================

class UrbanBuilder:
    def __init__(self, net_file="multi_junction.net.xml"):
        self.net_file = net_file
        self.lanes = []
        self.junctions = []
        self.polygons = [] # list of (id, type, color, layer, pts)
        self.load_network()
        
    def load_network(self):
        net_tree = ET.parse(self.net_file)
        net_root = net_tree.getroot()
        for lane in net_root.findall(".//lane"):
            shape = lane.get("shape")
            width = float(lane.get("width", 3.2))
            if shape:
                pts = parse_shape(shape)
                self.lanes.append((lane.get("id"), pts, width))
        for junc in net_root.findall(".//junction"):
            jtype = junc.get("type")
            shape = junc.get("shape")
            if shape and jtype != "internal":
                pts = parse_shape(shape)
                if len(pts) >= 3:
                    self.junctions.append((junc.get("id"), pts))
        print(f"Loaded network: {len(self.lanes)} lanes, {len(self.junctions)} junctions.")

    def check_collision(self, pts, buffer_dist=1.5, check_objects=True):
        for jid, junc_pts in self.junctions:
            if polygons_intersect(pts, junc_pts):
                return True
        for lid, lane_pts, width in self.lanes:
            min_allowed = (width / 2.0) + buffer_dist
            for i in range(len(lane_pts) - 1):
                lx1, ly1 = lane_pts[i]
                lx2, ly2 = lane_pts[i + 1]
                for px, py in pts:
                    if dist_point_segment(px, py, lx1, ly1, lx2, ly2) < min_allowed:
                        return True
        if check_objects:
            for pid, ptype, _, _, existing_pts in self.polygons:
                if ptype in ("building", "tree"):
                    if polygons_intersect(pts, existing_pts):
                        return True
        return False

    def add_poly(self, pid, ptype, color, layer, pts, strict=True):
        if strict:
            if self.check_collision(pts, buffer_dist=1.2, check_objects=(ptype in ("building", "tree"))):
                return False
        self.polygons.append((pid, ptype, color, layer, pts))
        return True

    def add_tree(self, tid, cx, cy, radius=2.5, color=None):
        if color is None:
            colors = ["0.18,0.48,0.22", "0.22,0.55,0.28", "0.28,0.62,0.32", "0.15,0.42,0.18"]
            color = random.choice(colors)
        pts = make_circle_poly(cx, cy, radius, num_pts=8)
        return self.add_poly(tid, "tree", color, layer=3, pts=pts, strict=True)

    def add_flower_bed(self, fid, pts, color=None):
        if color is None:
            colors = [
                "0.92,0.42,0.58", # Rose Pink
                "0.78,0.48,0.85", # Lavender Violet
                "0.96,0.75,0.20", # Marigold Yellow
                "0.88,0.28,0.35", # Crimson Floral
                "0.95,0.55,0.30", # Peach Blossom
            ]
            color = random.choice(colors)
        return self.add_poly(fid, "flower_bed", color, layer=2, pts=pts, strict=True)

    def add_park_lawn(self, pid, pts, color="0.32,0.65,0.36"):
        return self.add_poly(pid, "park", color, layer=1, pts=pts, strict=True)

    def add_garden_path(self, pid, pts, color="0.88,0.85,0.78"):
        return self.add_poly(pid, "pathway", color, layer=1, pts=pts, strict=True)

# Build Master Urban Environment
builder = UrbanBuilder("multi_junction.net.xml")
random.seed(101)

PALETTE_GLASS_TOWER = "0.85,0.92,0.98"
PALETTE_SANDSTONE = "0.95,0.90,0.82"
PALETTE_MODERN_WHITE = "0.98,0.98,0.99"
PALETTE_SLATE_GRAY = "0.86,0.89,0.92"
PALETTE_CONCRETE = "0.91,0.93,0.95"
PALETTE_BRICK = "0.88,0.75,0.68"
PALETTE_TERRACOTTA = "0.82,0.65,0.58"
PALETTE_DARK_CHARCOAL = "0.45,0.48,0.52"

# ------------------------------------------------------------------------------
# 1. SECTOR TL: NORTH-WEST HILLSIDE GARDEN PARK & RESIDENCES
# ------------------------------------------------------------------------------
builder.add_park_lawn("park_TL_north", make_rect(60, 960, 300, 1140), "0.30,0.62,0.34")
builder.add_flower_bed("garden_TL_rose_1", make_rect(80, 1060, 140, 1120), "0.92,0.42,0.58")
builder.add_flower_bed("garden_TL_lavender_1", make_rect(160, 1060, 220, 1120), "0.78,0.48,0.85")
builder.add_flower_bed("garden_TL_marigold_1", make_rect(240, 1060, 280, 1120), "0.96,0.75,0.20")
builder.add_flower_bed("garden_TL_crimson_1", make_rect(100, 980, 180, 1030), "0.88,0.28,0.35")
builder.add_flower_bed("garden_TL_tulip_1", make_rect(200, 980, 270, 1030), "0.95,0.55,0.30")
builder.add_garden_path("path_TL_main", make_rect(60, 1040, 300, 1050), "0.85,0.82,0.75")
builder.add_garden_path("path_TL_cross", make_rect(145, 960, 155, 1140), "0.85,0.82,0.75")

for tx in (70, 110, 150, 190, 230, 270, 290):
    builder.add_tree(f"tree_TL_park_{tx}_1", tx, 1130, radius=2.8)
    builder.add_tree(f"tree_TL_park_{tx}_2", tx, 970, radius=2.5)

builder.add_poly("bldg_TL_res_1", "building", PALETTE_SANDSTONE, 2, make_l_shape(60, 800, 140, 860, 30, 25, "top-right"))
builder.add_poly("bldg_TL_res_2", "building", PALETTE_MODERN_WHITE, 2, make_rect(160, 800, 220, 860))
builder.add_poly("bldg_TL_res_3", "building", PALETTE_SLATE_GRAY, 2, make_rect(240, 800, 300, 860))
builder.add_poly("bldg_TL_res_4", "building", PALETTE_GLASS_TOWER, 2, make_u_shape(60, 880, 140, 940, 35, 25))
builder.add_poly("bldg_TL_res_5", "building", PALETTE_BRICK, 2, make_rect(160, 880, 220, 940))
builder.add_poly("bldg_TL_res_6", "building", PALETTE_CONCRETE, 2, make_rect(240, 880, 300, 940))

builder.add_flower_bed("garden_TL_court_1", make_rect(142, 810, 158, 850), "0.92,0.42,0.58")
builder.add_flower_bed("garden_TL_court_2", make_rect(222, 810, 238, 850), "0.78,0.48,0.85")
builder.add_flower_bed("garden_TL_court_3", make_rect(142, 890, 158, 930), "0.96,0.75,0.20")
builder.add_flower_bed("garden_TL_court_4", make_rect(222, 890, 238, 930), "0.88,0.28,0.35")

for ty in (810, 850, 890, 930):
    builder.add_tree(f"tree_TL_west_{ty}", 50, ty, radius=2.4)
    builder.add_tree(f"tree_TL_east_{ty}", 310, ty, radius=2.4)

# ------------------------------------------------------------------------------
# 2. SECTOR TC: NORTH-CENTRAL COMMERCIAL & DIAGONAL BOULEVARD
# ------------------------------------------------------------------------------
builder.add_poly("bldg_TC_diag_1", "building", PALETTE_GLASS_TOWER, 2, make_rotated_rect(480, 880, 70, 35, 55))
builder.add_poly("bldg_TC_diag_2", "building", PALETTE_MODERN_WHITE, 2, make_rotated_rect(420, 970, 65, 35, 55))
builder.add_poly("bldg_TC_diag_3", "building", PALETTE_SLATE_GRAY, 2, make_rotated_rect(370, 1050, 60, 32, 55))

builder.add_poly("bldg_TC_corp_1", "building", PALETTE_GLASS_TOWER, 2, make_l_shape(600, 800, 720, 870, 40, 30, "top-right"))
builder.add_poly("bldg_TC_corp_2", "building", PALETTE_CONCRETE, 2, make_rect(750, 800, 880, 870))
builder.add_poly("bldg_TC_corp_3", "building", PALETTE_SANDSTONE, 2, make_u_shape(910, 800, 1030, 870, 45, 30))
builder.add_poly("bldg_TC_corp_4", "building", PALETTE_MODERN_WHITE, 2, make_rect(1060, 800, 1180, 870))

builder.add_poly("bldg_TC_corp_5", "building", PALETTE_SLATE_GRAY, 2, make_rect(600, 900, 720, 970))
builder.add_poly("bldg_TC_corp_6", "building", PALETTE_GLASS_TOWER, 2, make_rect(750, 900, 880, 970))
builder.add_poly("bldg_TC_corp_7", "building", PALETTE_BRICK, 2, make_rect(910, 900, 1030, 970))
builder.add_poly("bldg_TC_corp_8", "building", PALETTE_SANDSTONE, 2, make_rect(1060, 900, 1180, 970))

builder.add_poly("bldg_TC_corp_9", "building", PALETTE_MODERN_WHITE, 2, make_rect(600, 1000, 720, 1070))
builder.add_poly("bldg_TC_corp_10", "building", PALETTE_CONCRETE, 2, make_rect(750, 1000, 880, 1070))
builder.add_poly("bldg_TC_corp_11", "building", PALETTE_GLASS_TOWER, 2, make_rect(910, 1000, 1030, 1070))
builder.add_poly("bldg_TC_corp_12", "building", PALETTE_SLATE_GRAY, 2, make_rect(1060, 1000, 1180, 1070))

builder.add_park_lawn("park_TC_plaza", make_rect(600, 1090, 1180, 1160), "0.32,0.65,0.36")
builder.add_flower_bed("garden_TC_rose", make_rect(640, 1105, 740, 1145), "0.92,0.42,0.58")
builder.add_flower_bed("garden_TC_lavender", make_rect(780, 1105, 880, 1145), "0.78,0.48,0.85")
builder.add_flower_bed("garden_TC_marigold", make_rect(920, 1105, 1020, 1145), "0.96,0.75,0.20")
builder.add_flower_bed("garden_TC_crimson", make_rect(1060, 1105, 1150, 1145), "0.88,0.28,0.35")

for tx in range(610, 1180, 45):
    builder.add_tree(f"tree_TC_plaza_{tx}", tx, 1155, radius=2.6)

# Roadside tree buffer along TC
for tx in (620, 670, 770, 820, 930, 980, 1080, 1130):
    builder.add_tree(f"tree_TC_south_{tx}", tx, 788, radius=2.3)

# ------------------------------------------------------------------------------
# 3. SECTOR TR: FINANCIAL DISTRICT & CIVIC TOWERS
# ------------------------------------------------------------------------------
builder.add_poly("bldg_TR_fin_1", "building", PALETTE_GLASS_TOWER, 2, make_rect(1300, 800, 1430, 890))
builder.add_poly("bldg_TR_fin_2", "building", PALETTE_MODERN_WHITE, 2, make_l_shape(1460, 800, 1590, 890, 40, 35, "top-right"))
builder.add_poly("bldg_TR_fin_3", "building", PALETTE_DARK_CHARCOAL, 2, make_rect(1620, 800, 1750, 890))
builder.add_poly("bldg_TR_fin_4", "building", PALETTE_SANDSTONE, 2, make_rect(1770, 800, 1850, 890))

builder.add_poly("bldg_TR_fin_5", "building", PALETTE_SLATE_GRAY, 2, make_rect(1300, 920, 1430, 1010))
builder.add_poly("bldg_TR_fin_6", "building", PALETTE_GLASS_TOWER, 2, make_u_shape(1460, 920, 1590, 1010, 50, 35))
builder.add_poly("bldg_TR_fin_7", "building", PALETTE_CONCRETE, 2, make_rect(1620, 920, 1750, 1010))
builder.add_poly("bldg_TR_fin_8", "building", PALETTE_MODERN_WHITE, 2, make_rect(1770, 920, 1850, 1010))

builder.add_poly("bldg_TR_fin_9", "building", PALETTE_BRICK, 2, make_rect(1300, 1040, 1430, 1130))
builder.add_poly("bldg_TR_fin_10", "building", PALETTE_SANDSTONE, 2, make_rect(1460, 1040, 1590, 1130))
builder.add_poly("bldg_TR_fin_11", "building", PALETTE_GLASS_TOWER, 2, make_rect(1620, 1040, 1750, 1130))
builder.add_poly("bldg_TR_fin_12", "building", PALETTE_SLATE_GRAY, 2, make_rect(1770, 1040, 1850, 1130))

builder.add_flower_bed("garden_TR_atrium_1", make_rect(1434, 820, 1456, 870), "0.92,0.42,0.58")
builder.add_flower_bed("garden_TR_atrium_2", make_rect(1594, 820, 1616, 870), "0.78,0.48,0.85")
builder.add_flower_bed("garden_TR_atrium_3", make_rect(1434, 940, 1456, 990), "0.96,0.75,0.20")
builder.add_flower_bed("garden_TR_atrium_4", make_rect(1594, 940, 1616, 990), "0.88,0.28,0.35")

for ty in (810, 850, 930, 970, 1050, 1090):
    builder.add_tree(f"tree_TR_west_{ty}", 1292, ty, radius=2.5)
    builder.add_tree(f"tree_TR_east_{ty}", 1855, ty, radius=2.5)

for tx in (1330, 1380, 1490, 1540, 1650, 1700, 1800):
    builder.add_tree(f"tree_TR_south_{tx}", tx, 788, radius=2.3)

# ------------------------------------------------------------------------------
# 4. SECTOR TE: NORTH-EAST COMMERCIAL & BOTANICAL ESTATE
# ------------------------------------------------------------------------------
builder.add_poly("bldg_TE_comm_1", "building", PALETTE_MODERN_WHITE, 2, make_rect(1960, 800, 2080, 890))
builder.add_poly("bldg_TE_comm_2", "building", PALETTE_GLASS_TOWER, 2, make_l_shape(2110, 800, 2230, 890, 35, 30, "top-right"))
builder.add_poly("bldg_TE_comm_3", "building", PALETTE_SANDSTONE, 2, make_rect(2260, 800, 2360, 890))

builder.add_poly("bldg_TE_comm_4", "building", PALETTE_SLATE_GRAY, 2, make_rect(1960, 920, 2080, 1010))
builder.add_poly("bldg_TE_comm_5", "building", PALETTE_CONCRETE, 2, make_rect(2110, 920, 2230, 1010))
builder.add_poly("bldg_TE_comm_6", "building", PALETTE_BRICK, 2, make_rect(2260, 920, 2360, 1010))

builder.add_park_lawn("park_TE_estate", make_rect(1960, 1035, 2360, 1150), "0.30,0.64,0.35")
builder.add_flower_bed("garden_TE_rose", make_rect(1980, 1055, 2070, 1130), "0.92,0.42,0.58")
builder.add_flower_bed("garden_TE_lavender", make_rect(2100, 1055, 2190, 1130), "0.78,0.48,0.85")
builder.add_flower_bed("garden_TE_marigold", make_rect(2220, 1055, 2310, 1130), "0.96,0.75,0.20")

for tx in range(1970, 2360, 40):
    builder.add_tree(f"tree_TE_park_{tx}", tx, 1140, radius=2.7)

for tx in (1980, 2030, 2130, 2180, 2280, 2330):
    builder.add_tree(f"tree_TE_south_{tx}", tx, 788, radius=2.3)

# ------------------------------------------------------------------------------
# 5. SECTOR ML: WEST MID-TOWN RESIDENTIAL & COURTYARDS
# ------------------------------------------------------------------------------
builder.add_poly("bldg_ML_apt_1", "building", PALETTE_SANDSTONE, 2, make_rect(60, 450, 170, 520))
builder.add_poly("bldg_ML_apt_2", "building", PALETTE_MODERN_WHITE, 2, make_l_shape(200, 450, 310, 520, 35, 25, "top-right"))
builder.add_poly("bldg_ML_apt_3", "building", PALETTE_SLATE_GRAY, 2, make_rect(340, 450, 450, 520))

builder.add_poly("bldg_ML_apt_4", "building", PALETTE_GLASS_TOWER, 2, make_u_shape(60, 550, 170, 620, 40, 25))
builder.add_poly("bldg_ML_apt_5", "building", PALETTE_BRICK, 2, make_rect(200, 550, 310, 620))
builder.add_poly("bldg_ML_apt_6", "building", PALETTE_CONCRETE, 2, make_rect(340, 550, 450, 620))

builder.add_poly("bldg_ML_apt_7", "building", PALETTE_MODERN_WHITE, 2, make_rect(60, 645, 170, 710))
builder.add_poly("bldg_ML_apt_8", "building", PALETTE_SANDSTONE, 2, make_rect(200, 645, 310, 710))
builder.add_poly("bldg_ML_apt_9", "building", PALETTE_GLASS_TOWER, 2, make_rect(340, 645, 450, 710))

builder.add_flower_bed("garden_ML_court_1", make_rect(174, 460, 196, 510), "0.92,0.42,0.58")
builder.add_flower_bed("garden_ML_court_2", make_rect(314, 460, 336, 510), "0.78,0.48,0.85")
builder.add_flower_bed("garden_ML_court_3", make_rect(174, 560, 196, 610), "0.96,0.75,0.20")
builder.add_flower_bed("garden_ML_court_4", make_rect(314, 560, 336, 610), "0.88,0.28,0.35")

for ty in (460, 500, 560, 600, 660, 700):
    builder.add_tree(f"tree_ML_west_{ty}", 50, ty, radius=2.5)

for tx in (80, 130, 220, 270, 360, 410):
    builder.add_tree(f"tree_ML_south_{tx}", tx, 438, radius=2.3)
    builder.add_tree(f"tree_ML_north_{tx}", tx, 718, radius=2.3)

# ------------------------------------------------------------------------------
# 6. SECTOR MC: CENTRAL TECHNOLOGY PARK & ATRIUM
# ------------------------------------------------------------------------------
builder.add_poly("bldg_MC_tech_1", "building", PALETTE_GLASS_TOWER, 2, make_rect(620, 450, 730, 520))
builder.add_poly("bldg_MC_tech_2", "building", PALETTE_MODERN_WHITE, 2, make_l_shape(760, 450, 870, 520, 35, 25, "top-right"))
builder.add_poly("bldg_MC_tech_3", "building", PALETTE_SLATE_GRAY, 2, make_rect(900, 450, 1010, 520))
builder.add_poly("bldg_MC_tech_4", "building", PALETTE_CONCRETE, 2, make_rect(1040, 450, 1140, 520))

builder.add_poly("bldg_MC_tech_5", "building", PALETTE_DARK_CHARCOAL, 2, make_u_shape(620, 550, 730, 620, 40, 25))
builder.add_poly("bldg_MC_tech_6", "building", PALETTE_GLASS_TOWER, 2, make_rect(760, 550, 870, 620))
builder.add_poly("bldg_MC_tech_7", "building", PALETTE_SANDSTONE, 2, make_rect(900, 550, 1010, 620))
builder.add_poly("bldg_MC_tech_8", "building", PALETTE_MODERN_WHITE, 2, make_rect(1040, 550, 1140, 620))

builder.add_poly("bldg_MC_tech_9", "building", PALETTE_BRICK, 2, make_rect(620, 645, 730, 710))
builder.add_poly("bldg_MC_tech_10", "building", PALETTE_SLATE_GRAY, 2, make_rect(760, 645, 870, 710))
builder.add_poly("bldg_MC_tech_11", "building", PALETTE_GLASS_TOWER, 2, make_rect(900, 645, 1010, 710))
builder.add_poly("bldg_MC_tech_12", "building", PALETTE_CONCRETE, 2, make_rect(1040, 645, 1140, 710))

builder.add_flower_bed("garden_MC_atrium_1", make_rect(734, 460, 756, 510), "0.92,0.42,0.58")
builder.add_flower_bed("garden_MC_atrium_2", make_rect(874, 460, 896, 510), "0.78,0.48,0.85")
builder.add_flower_bed("garden_MC_atrium_3", make_rect(1014, 460, 1036, 510), "0.96,0.75,0.20")
builder.add_flower_bed("garden_MC_atrium_4", make_rect(734, 560, 756, 610), "0.88,0.28,0.35")
builder.add_flower_bed("garden_MC_atrium_5", make_rect(874, 560, 896, 610), "0.95,0.55,0.30")
builder.add_flower_bed("garden_MC_atrium_6", make_rect(1014, 560, 1036, 610), "0.92,0.42,0.58")

for tx in (630, 675, 770, 815, 910, 955, 1050, 1095):
    builder.add_tree(f"tree_MC_south_{tx}", tx, 442, radius=2.3)
    builder.add_tree(f"tree_MC_north_{tx}", tx, 718, radius=2.3)

# ------------------------------------------------------------------------------
# 7. SECTOR MR: MEDICAL & RETAIL COMPLEX
# ------------------------------------------------------------------------------
builder.add_poly("bldg_MR_med_1", "building", PALETTE_MODERN_WHITE, 2, make_rect(1280, 450, 1400, 525))
builder.add_poly("bldg_MR_med_2", "building", PALETTE_GLASS_TOWER, 2, make_l_shape(1430, 450, 1550, 525, 35, 25, "top-right"))
builder.add_poly("bldg_MR_med_3", "building", PALETTE_SANDSTONE, 2, make_rect(1580, 450, 1700, 525))
builder.add_poly("bldg_MR_med_4", "building", PALETTE_CONCRETE, 2, make_rect(1730, 450, 1845, 525))

builder.add_poly("bldg_MR_med_5", "building", PALETTE_SLATE_GRAY, 2, make_u_shape(1280, 545, 1400, 620, 40, 25))
builder.add_poly("bldg_MR_med_6", "building", PALETTE_MODERN_WHITE, 2, make_rect(1430, 545, 1550, 620))
builder.add_poly("bldg_MR_med_7", "building", PALETTE_GLASS_TOWER, 2, make_rect(1580, 545, 1700, 620))
builder.add_poly("bldg_MR_med_8", "building", PALETTE_BRICK, 2, make_rect(1730, 545, 1845, 620))

builder.add_poly("bldg_MR_med_9", "building", PALETTE_SANDSTONE, 2, make_rect(1280, 640, 1400, 710))
builder.add_poly("bldg_MR_med_10", "building", PALETTE_CONCRETE, 2, make_rect(1430, 640, 1550, 710))
builder.add_poly("bldg_MR_med_11", "building", PALETTE_MODERN_WHITE, 2, make_rect(1580, 640, 1700, 710))
builder.add_poly("bldg_MR_med_12", "building", PALETTE_GLASS_TOWER, 2, make_rect(1730, 640, 1845, 710))

builder.add_flower_bed("garden_MR_court_1", make_rect(1404, 465, 1426, 515), "0.92,0.42,0.58")
builder.add_flower_bed("garden_MR_court_2", make_rect(1554, 465, 1576, 515), "0.78,0.48,0.85")
builder.add_flower_bed("garden_MR_court_3", make_rect(1704, 465, 1726, 515), "0.96,0.75,0.20")
builder.add_flower_bed("garden_MR_court_4", make_rect(1404, 560, 1426, 610), "0.88,0.28,0.35")
builder.add_flower_bed("garden_MR_court_5", make_rect(1554, 560, 1576, 610), "0.95,0.55,0.30")
builder.add_flower_bed("garden_MR_court_6", make_rect(1704, 560, 1726, 610), "0.92,0.42,0.58")

for tx in (1300, 1350, 1450, 1500, 1600, 1650, 1750, 1800):
    builder.add_tree(f"tree_MR_south_{tx}", tx, 442, radius=2.3)
    builder.add_tree(f"tree_MR_north_{tx}", tx, 718, radius=2.3)

# ------------------------------------------------------------------------------
# 8. SECTOR ME: EAST CORRIDOR COMMERCIAL COMPLEX
# ------------------------------------------------------------------------------
builder.add_poly("bldg_ME_com_1", "building", PALETTE_GLASS_TOWER, 2, make_rect(1960, 450, 2080, 525))
builder.add_poly("bldg_ME_com_2", "building", PALETTE_MODERN_WHITE, 2, make_l_shape(2105, 450, 2225, 525, 35, 25, "top-right"))
builder.add_poly("bldg_ME_com_3", "building", PALETTE_SANDSTONE, 2, make_rect(2250, 450, 2360, 525))

builder.add_poly("bldg_ME_com_4", "building", PALETTE_SLATE_GRAY, 2, make_rect(1960, 545, 2080, 620))
builder.add_poly("bldg_ME_com_5", "building", PALETTE_CONCRETE, 2, make_rect(2105, 545, 2225, 620))
builder.add_poly("bldg_ME_com_6", "building", PALETTE_BRICK, 2, make_rect(2250, 545, 2360, 620))

builder.add_poly("bldg_ME_com_7", "building", PALETTE_MODERN_WHITE, 2, make_rect(1960, 640, 2080, 710))
builder.add_poly("bldg_ME_com_8", "building", PALETTE_GLASS_TOWER, 2, make_rect(2105, 640, 2225, 710))
builder.add_poly("bldg_ME_com_9", "building", PALETTE_SANDSTONE, 2, make_rect(2250, 640, 2360, 710))

builder.add_flower_bed("garden_ME_promenade_1", make_rect(2084, 465, 2101, 515), "0.92,0.42,0.58")
builder.add_flower_bed("garden_ME_promenade_2", make_rect(2229, 465, 2246, 515), "0.78,0.48,0.85")
builder.add_flower_bed("garden_ME_promenade_3", make_rect(2084, 560, 2101, 610), "0.96,0.75,0.20")
builder.add_flower_bed("garden_ME_promenade_4", make_rect(2229, 560, 2246, 610), "0.88,0.28,0.35")

for tx in (1980, 2030, 2130, 2180, 2280, 2330):
    builder.add_tree(f"tree_ME_south_{tx}", tx, 442, radius=2.3)
    builder.add_tree(f"tree_ME_north_{tx}", tx, 718, radius=2.3)

# ------------------------------------------------------------------------------
# 9. SECTOR BL: SOUTH-WEST CIVIC & EDUCATIONAL CAMPUS
# ------------------------------------------------------------------------------
builder.add_poly("bldg_BL_edu_1", "building", PALETTE_SANDSTONE, 2, make_l_shape(60, 60, 180, 140, 40, 30, "top-right"))
builder.add_poly("bldg_BL_edu_2", "building", PALETTE_MODERN_WHITE, 2, make_rect(210, 60, 330, 140))
builder.add_poly("bldg_BL_edu_3", "building", PALETTE_SLATE_GRAY, 2, make_rect(360, 60, 480, 140))

builder.add_poly("bldg_BL_edu_4", "building", PALETTE_BRICK, 2, make_rect(60, 170, 180, 250))
builder.add_poly("bldg_BL_edu_5", "building", PALETTE_GLASS_TOWER, 2, make_u_shape(210, 170, 330, 250, 45, 30))
builder.add_poly("bldg_BL_edu_6", "building", PALETTE_CONCRETE, 2, make_rect(360, 170, 480, 250))

builder.add_poly("bldg_BL_edu_7", "building", PALETTE_MODERN_WHITE, 2, make_rect(60, 275, 180, 350))
builder.add_poly("bldg_BL_edu_8", "building", PALETTE_SANDSTONE, 2, make_rect(210, 275, 330, 350))
builder.add_poly("bldg_BL_edu_9", "building", PALETTE_GLASS_TOWER, 2, make_rect(360, 275, 480, 350))

builder.add_flower_bed("garden_BL_quad_1", make_rect(184, 80, 206, 130), "0.92,0.42,0.58")
builder.add_flower_bed("garden_BL_quad_2", make_rect(334, 80, 356, 130), "0.78,0.48,0.85")
builder.add_flower_bed("garden_BL_quad_3", make_rect(184, 190, 206, 240), "0.96,0.75,0.20")
builder.add_flower_bed("garden_BL_quad_4", make_rect(334, 190, 356, 240), "0.88,0.28,0.35")

for tx in (75, 130, 225, 280, 375, 430):
    builder.add_tree(f"tree_BL_south_{tx}", tx, 50, radius=2.5)

# ------------------------------------------------------------------------------
# 10. SECTOR BM: GRAND BOTANICAL GARDENS & RESIDENTIAL ESTATE
# ------------------------------------------------------------------------------
builder.add_park_lawn("park_BM_botanical", make_rect(620, 60, 880, 350), "0.28,0.64,0.32")
builder.add_flower_bed("garden_BM_rose_parterre", make_rect(640, 240, 740, 330), "0.92,0.42,0.58")
builder.add_flower_bed("garden_BM_lavender_parterre", make_rect(760, 240, 860, 330), "0.78,0.48,0.85")
builder.add_flower_bed("garden_BM_marigold_parterre", make_rect(640, 80, 740, 170), "0.96,0.75,0.20")
builder.add_flower_bed("garden_BM_crimson_parterre", make_rect(760, 80, 860, 170), "0.88,0.28,0.35")
builder.add_flower_bed("garden_BM_center_circle", make_rect(700, 185, 800, 225), "0.95,0.55,0.30")

builder.add_garden_path("path_BM_main", make_rect(620, 195, 880, 215), "0.88,0.85,0.78")
builder.add_garden_path("path_BM_cross", make_rect(740, 60, 760, 350), "0.88,0.85,0.78")

for tx in (630, 690, 750, 810, 870):
    builder.add_tree(f"tree_BM_north_{tx}", tx, 340, radius=2.7)
    builder.add_tree(f"tree_BM_south_{tx}", tx, 70, radius=2.7)
for ty in (130, 190, 250, 310):
    builder.add_tree(f"tree_BM_west_{ty}", 630, ty, radius=2.5)
    builder.add_tree(f"tree_BM_east_{ty}", 870, ty, radius=2.5)

builder.add_poly("bldg_BM_res_1", "building", PALETTE_SANDSTONE, 2, make_rect(910, 60, 1010, 140))
builder.add_poly("bldg_BM_res_2", "building", PALETTE_MODERN_WHITE, 2, make_l_shape(1040, 60, 1140, 140, 35, 25, "top-right"))
builder.add_poly("bldg_BM_res_3", "building", PALETTE_SLATE_GRAY, 2, make_u_shape(910, 170, 1010, 250, 40, 25))
builder.add_poly("bldg_BM_res_4", "building", PALETTE_GLASS_TOWER, 2, make_rect(1040, 170, 1140, 250))
builder.add_poly("bldg_BM_res_5", "building", PALETTE_CONCRETE, 2, make_rect(910, 275, 1010, 350))
builder.add_poly("bldg_BM_res_6", "building", PALETTE_BRICK, 2, make_rect(1040, 275, 1140, 350))

builder.add_flower_bed("garden_BM_court_1", make_rect(1014, 80, 1036, 130), "0.92,0.42,0.58")
builder.add_flower_bed("garden_BM_court_2", make_rect(1014, 190, 1036, 240), "0.78,0.48,0.85")
builder.add_flower_bed("garden_BM_court_3", make_rect(1014, 290, 1036, 340), "0.96,0.75,0.20")

# ------------------------------------------------------------------------------
# 11. SECTOR BR: COMMUNITY RECREATION & APARTMENTS
# ------------------------------------------------------------------------------
builder.add_poly("bldg_BR_com_1", "building", PALETTE_MODERN_WHITE, 2, make_rect(1270, 60, 1390, 140))
builder.add_poly("bldg_BR_com_2", "building", PALETTE_SANDSTONE, 2, make_l_shape(1420, 60, 1540, 140, 35, 25, "top-right"))
builder.add_poly("bldg_BR_com_3", "building", PALETTE_GLASS_TOWER, 2, make_rect(1570, 60, 1690, 140))
builder.add_poly("bldg_BR_com_4", "building", PALETTE_CONCRETE, 2, make_rect(1720, 60, 1845, 140))

builder.add_poly("bldg_BR_com_5", "building", PALETTE_SLATE_GRAY, 2, make_u_shape(1270, 170, 1390, 250, 40, 25))
builder.add_poly("bldg_BR_com_6", "building", PALETTE_BRICK, 2, make_rect(1420, 170, 1540, 250))
builder.add_poly("bldg_BR_com_7", "building", PALETTE_MODERN_WHITE, 2, make_rect(1570, 170, 1690, 250))
builder.add_poly("bldg_BR_com_8", "building", PALETTE_SANDSTONE, 2, make_rect(1720, 170, 1845, 250))

builder.add_poly("bldg_BR_com_9", "building", PALETTE_GLASS_TOWER, 2, make_rect(1270, 275, 1390, 350))
builder.add_poly("bldg_BR_com_10", "building", PALETTE_CONCRETE, 2, make_rect(1420, 275, 1540, 350))
builder.add_poly("bldg_BR_com_11", "building", PALETTE_SLATE_GRAY, 2, make_rect(1570, 275, 1690, 350))
builder.add_poly("bldg_BR_com_12", "building", PALETTE_MODERN_WHITE, 2, make_rect(1720, 275, 1845, 350))

builder.add_flower_bed("garden_BR_court_1", make_rect(1394, 80, 1416, 130), "0.92,0.42,0.58")
builder.add_flower_bed("garden_BR_court_2", make_rect(1544, 80, 1566, 130), "0.78,0.48,0.85")
builder.add_flower_bed("garden_BR_court_3", make_rect(1694, 80, 1716, 130), "0.96,0.75,0.20")
builder.add_flower_bed("garden_BR_court_4", make_rect(1394, 190, 1416, 240), "0.88,0.28,0.35")
builder.add_flower_bed("garden_BR_court_5", make_rect(1544, 190, 1566, 240), "0.95,0.55,0.30")
builder.add_flower_bed("garden_BR_court_6", make_rect(1694, 190, 1716, 240), "0.92,0.42,0.58")

for tx in (1300, 1350, 1450, 1500, 1600, 1650, 1750, 1800):
    builder.add_tree(f"tree_BR_south_{tx}", tx, 50, radius=2.5)

# ------------------------------------------------------------------------------
# 12. SECTOR BE: SOUTH-EAST BUSINESS PARK & GREEN BUFFER
# ------------------------------------------------------------------------------
builder.add_poly("bldg_BE_biz_1", "building", PALETTE_GLASS_TOWER, 2, make_rect(1960, 60, 2080, 140))
builder.add_poly("bldg_BE_biz_2", "building", PALETTE_MODERN_WHITE, 2, make_l_shape(2105, 60, 2225, 140, 35, 25, "top-right"))
builder.add_poly("bldg_BE_biz_3", "building", PALETTE_SANDSTONE, 2, make_rect(2250, 60, 2360, 140))

builder.add_poly("bldg_BE_biz_4", "building", PALETTE_SLATE_GRAY, 2, make_rect(1960, 170, 2080, 250))
builder.add_poly("bldg_BE_biz_5", "building", PALETTE_CONCRETE, 2, make_rect(2105, 170, 2225, 250))
builder.add_poly("bldg_BE_biz_6", "building", PALETTE_BRICK, 2, make_rect(2250, 170, 2360, 250))

builder.add_poly("bldg_BE_biz_7", "building", PALETTE_MODERN_WHITE, 2, make_rect(1960, 275, 2080, 350))
builder.add_poly("bldg_BE_biz_8", "building", PALETTE_GLASS_TOWER, 2, make_rect(2105, 275, 2225, 350))
builder.add_poly("bldg_BE_biz_9", "building", PALETTE_SANDSTONE, 2, make_rect(2250, 275, 2360, 350))

builder.add_flower_bed("garden_BE_prom_1", make_rect(2084, 80, 2101, 130), "0.92,0.42,0.58")
builder.add_flower_bed("garden_BE_prom_2", make_rect(2229, 80, 2246, 130), "0.78,0.48,0.85")
builder.add_flower_bed("garden_BE_prom_3", make_rect(2084, 190, 2101, 240), "0.96,0.75,0.20")
builder.add_flower_bed("garden_BE_prom_4", make_rect(2229, 190, 2246, 240), "0.88,0.28,0.35")

for tx in (1980, 2030, 2130, 2180, 2280, 2330):
    builder.add_tree(f"tree_BE_south_{tx}", tx, 50, radius=2.5)

# ------------------------------------------------------------------------------
# SAVE TO MULTI_JUNCTION.ADD.XML
# ------------------------------------------------------------------------------
print(f"Total objects generated: {len(builder.polygons)}")

xml_lines = ["<additional>"]
for pid, ptype, color, layer, pts in builder.polygons:
    shape_str = format_shape(pts)
    xml_lines.append(f'    <poly id="{pid}" type="{ptype}" color="{color}" layer="{layer}" fill="true" shape="{shape_str}"/>')
xml_lines.append("</additional>\n")

with open("multi_junction.add.xml", "w") as f:
    f.write("\n".join(xml_lines))

print("Successfully written to multi_junction.add.xml!")
