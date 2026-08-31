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

def is_poly_strictly_safe(poly_pts, lanes, junctions, min_clearance=25.0):
    # 1. Check direct intersection with all junction polygons
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

    # 2. Check distance from poly edges to lane centerlines
    for lane_pts, width in lanes:
        required_dist = (width / 2.0) + min_clearance
        for i in range(len(lane_pts) - 1):
            lx1, ly1 = lane_pts[i]
            lx2, ly2 = lane_pts[i + 1]
            for px, py in poly_pts:
                if dist_point_segment(px, py, lx1, ly1, lx2, ly2) < required_dist:
                    return False
    return True

def generate():
    lanes, junctions = load_net()
    print(f"Loaded {len(lanes)} lanes and {len(junctions)} junctions.")

    # High-clearance blocks located strictly in block interiors
    raw_blocks = [
        ("TL", -250, -50, 580, 800),
        ("TM", 550, 850, 580, 880),
        ("TR", 1050, 1480, 580, 880),
        ("TE", 1720, 1980, 580, 880),

        ("ML", -250, 100, 240, 420),
        ("CM", 400, 800, 240, 420),
        ("CR", 1050, 1480, 240, 420),
        ("CE", 1720, 1980, 240, 420),

        ("BL", -250, 100, -160, 60),
        ("BM", 400, 800, -160, 60),
        ("BR", 1050, 1480, -160, 60),
        ("BE", 1720, 1980, -160, 60),
    ]

    polys = []

    for name, xmin, xmax, ymin, ymax in raw_blocks:
        nx = 2
        ny = 2
        dx = (xmax - xmin) / nx
        dy = (ymax - ymin) / ny

        for ix in range(nx):
            for iy in range(ny):
                bx1 = xmin + ix * dx + 12
                bx2 = xmin + (ix + 1) * dx - 12
                by1 = ymin + iy * dy + 12
                by2 = ymin + (iy + 1) * dy - 12

                candidate = [(bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2)]
                if is_poly_strictly_safe(candidate, lanes, junctions, min_clearance=25.0):
                    b_id = f"bldg_{name}_{ix+1}_{iy+1}"
                    color = "0.99,0.99,0.99" if (ix + iy) % 2 == 0 else "0.94,0.94,0.96"
                    shape_str = f"{bx1:.1f},{by1:.1f} {bx2:.1f},{by1:.1f} {bx2:.1f},{by2:.1f} {bx1:.1f},{by2:.1f}"
                    polys.append((b_id, "building", color, 2, shape_str))

        # Add safe parks in central blocks
        if name in ["TM", "CM", "TR", "BM"]:
            px1 = xmin + dx * 0.3 + 15
            px2 = xmax - dx * 0.3 - 15
            py1 = ymin + dy * 0.3 + 15
            py2 = ymax - dy * 0.3 - 15
            if px2 > px1 and py2 > py1:
                p_cand = [(px1, py1), (px2, py1), (px2, py2), (px1, py2)]
                if is_poly_strictly_safe(p_cand, lanes, junctions, min_clearance=28.0):
                    park_id = f"park_{name}"
                    shape_str = f"{px1:.1f},{py1:.1f} {px2:.1f},{py1:.1f} {px2:.1f},{py2:.1f} {px1:.1f},{py2:.1f}"
                    polys.append((park_id, "park", "0.18,0.50,0.22", 1, shape_str))

    # Add Top-Left Depot
    dx1, dx2, dy1, dy2 = -240, -100, 620, 780
    d_cand = [(dx1, dy1), (dx2, dy1), (dx2, dy2), (dx1, dy2)]
    if is_poly_strictly_safe(d_cand, lanes, junctions, min_clearance=25.0):
        polys.append(("depot_ground", "commercial", "0.82,0.85,0.88", 0, f"{dx1},{dy1} {dx2},{dy1} {dx2},{dy2} {dx1},{dy2}"))
        for s in range(2):
            sy1 = dy1 + 25 + s * 65
            sy2 = sy1 + 25
            polys.append((f"depot_strip_{s+1}", "commercial", "0.70,0.74,0.78", 1, f"{dx1+15},{sy1} {dx2-15},{sy1} {dx2-15},{sy2} {dx1+15},{sy2}"))

    # Write multi_junction.add.xml
    with open("multi_junction.add.xml", "w") as f:
        f.write("<additional>\n")
        for pid, ptype, color, layer, shape in polys:
            f.write(f'    <poly id="{pid}" type="{ptype}" color="{color}" layer="{layer}" fill="true" shape="{shape}"/>\n')
        f.write("</additional>\n")

    print(f"Generated {len(polys)} strictly non-conflicting buildings/parks with 25m+ clearances.")

if __name__ == "__main__":
    generate()
