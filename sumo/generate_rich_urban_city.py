import xml.etree.ElementTree as ET
import math

def parse_shape(shape_str):
    pts = []
    for pair in shape_str.strip().split():
        x, y = map(float, pair.split(','))
        pts.append((x, y))
    return pts

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

def load_net():
    tree = ET.parse("multi_junction.net.xml")
    root = tree.getroot()
    lanes = []
    for lane in root.findall(".//lane"):
        shape = lane.get("shape")
        width = float(lane.get("width", 3.2))
        if shape:
            lanes.append((parse_shape(shape), width))
    junctions = []
    for junc in root.findall(".//junction"):
        shape = junc.get("shape")
        jtype = junc.get("type")
        if shape and jtype != "internal":
            pts = parse_shape(shape)
            if len(pts) >= 3:
                junctions.append(pts)
    return lanes, junctions

def is_safe_from_roads(poly_pts, lanes, junctions, min_clearance=25.0):
    for junc in junctions:
        if polygons_intersect(poly_pts, junc):
            return False
        n = len(junc)
        for i in range(n):
            jx1, jy1 = junc[i]
            jx2, jy2 = junc[(i + 1) % n]
            for px, py in poly_pts:
                if dist_point_segment(px, py, jx1, jy1, jx2, jy2) < min_clearance:
                    return False
    for lane_pts, width in lanes:
        required_dist = (width / 2.0) + min_clearance
        for i in range(len(lane_pts) - 1):
            lx1, ly1 = lane_pts[i]
            lx2, ly2 = lane_pts[i + 1]
            for px, py in poly_pts:
                if dist_point_segment(px, py, lx1, ly1, lx2, ly2) < required_dist:
                    return False
    return True

def create_tree_poly(cx, cy, r=5.0):
    # 8-sided polygon approximating a tree crown
    pts = []
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts

def generate():
    lanes, junctions = load_net()
    print(f"Loaded {len(lanes)} lanes and {len(junctions)} junctions.")

    blocks = [
        # Top Row (y > 550)
        ("TL", -230, -50, 600, 800),
        ("TM", 540, 860, 600, 860),
        ("TR", 1060, 1500, 600, 860),
        ("TE", 1720, 2020, 600, 860),

        # Middle Row (200 < y < 450)
        ("ML", -230, 100, 230, 420),
        ("CM", 480, 800, 230, 420),
        ("CR", 1060, 1500, 230, 420),
        ("CE", 1720, 2020, 230, 420),

        # Bottom Row (-200 < y < 70)
        ("BL", -230, 120, -180, 50),
        ("BM", 360, 800, -180, 50),
        ("BR", 1000, 1500, -180, 50),
        ("BE", 1720, 2020, -180, 50),
    ]

    placed_polys = []

    # Palette of realistic colors
    bldg_colors = [
        "0.99,0.99,0.99", "0.94,0.94,0.96", "0.96,0.91,0.87",
        "0.88,0.90,0.93", "0.92,0.88,0.84", "0.97,0.97,0.98"
    ]
    tree_colors = [
        "0.15,0.48,0.18", "0.18,0.55,0.22", "0.12,0.42,0.15", "0.22,0.60,0.25"
    ]

    # 1. Place dense array of buildings in each block
    for name, xmin, xmax, ymin, ymax in blocks:
        nx, ny = 3, 2
        dx = (xmax - xmin) / nx
        dy = (ymax - ymin) / ny

        for ix in range(nx):
            for iy in range(ny):
                bx1 = xmin + ix * dx + 10
                bx2 = xmin + (ix + 1) * dx - 10
                by1 = ymin + iy * dy + 10
                by2 = ymin + (iy + 1) * dy - 10

                cand = [(bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2)]
                
                # Check safety against roads
                if is_safe_from_roads(cand, lanes, junctions, min_clearance=24.0):
                    # Check safety against already placed polys
                    conflict = False
                    for _, _, _, _, existing_pts in placed_polys:
                        if polygons_intersect(cand, existing_pts):
                            conflict = True
                            break
                    if not conflict:
                        color = bldg_colors[(ix + iy * 2) % len(bldg_colors)]
                        b_id = f"bldg_{name}_{ix+1}_{iy+1}"
                        placed_polys.append((b_id, "building", color, 2, cand))

    # 2. Place Trees in open spaces between buildings and inside block courtyards
    tree_count = 0
    for name, xmin, xmax, ymin, ymax in blocks:
        # Create a fine grid of candidate tree locations
        gx_steps = 7
        gy_steps = 5
        for gx in range(gx_steps):
            for gy in range(gy_steps):
                tx = xmin + (gx + 0.5) * ((xmax - xmin) / gx_steps)
                ty = ymin + (gy + 0.5) * ((ymax - ymin) / gy_steps)
                
                tree_cand = create_tree_poly(tx, ty, r=5.5)
                
                # Must be 25m+ safe from all roads
                if is_safe_from_roads(tree_cand, lanes, junctions, min_clearance=25.0):
                    # Must NOT intersect any existing building or tree
                    conflict = False
                    for _, ptype, _, _, existing_pts in placed_polys:
                        if polygons_intersect(tree_cand, existing_pts):
                            conflict = True
                            break
                        # Also keep 3m buffer between trees
                        if ptype == "tree":
                            for px, py in tree_cand:
                                for ex, ey in existing_pts:
                                    if math.hypot(px - ex, py - ey) < 3.0:
                                        conflict = True
                                        break
                                if conflict:
                                    break
                        if conflict:
                            break
                    
                    if not conflict:
                        tree_count += 1
                        t_id = f"tree_{name}_{tree_count}"
                        t_color = tree_colors[tree_count % len(tree_colors)]
                        placed_polys.append((t_id, "tree", t_color, 3, tree_cand))

    # Write multi_junction.add.xml
    with open("multi_junction.add.xml", "w") as f:
        f.write("<additional>\n")
        for pid, ptype, color, layer, pts in placed_polys:
            shape_str = " ".join([f"{x:.1f},{y:.1f}" for x, y in pts])
            f.write(f'    <poly id="{pid}" type="{ptype}" color="{color}" layer="{layer}" fill="true" shape="{shape_str}"/>\n')
        f.write("</additional>\n")

    bldg_total = sum(1 for _, ptype, _, _, _ in placed_polys if ptype == "building")
    tree_total = sum(1 for _, ptype, _, _, _ in placed_polys if ptype == "tree")
    print(f"SUCCESS: Generated {bldg_total} buildings and {tree_total} trees ({len(placed_polys)} total objects).")

if __name__ == "__main__":
    generate()
