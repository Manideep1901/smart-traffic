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

def is_strictly_safe(poly_pts, lanes, junctions, min_clearance=30.0):
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

def generate():
    lanes, junctions = load_net()
    print(f"Loaded {len(lanes)} lanes and {len(junctions)} junctions.")

    # 12 clean urban block bounding boxes
    blocks = [
        # Top Row (y > 550)
        ("TL", -230, -50, 600, 800),
        ("TM", 550, 850, 600, 850),
        ("TR", 1080, 1500, 600, 850),
        ("TE", 1720, 2000, 600, 850),

        # Middle Row (200 < y < 450)
        ("ML", -230, 100, 240, 420),
        ("CM", 480, 800, 240, 420),
        ("CR", 1080, 1500, 240, 420),
        ("CE", 1720, 2000, 240, 420),

        # Bottom Row (-200 < y < 80)
        ("BL", -230, 120, -180, 50),
        ("BM", 380, 780, -180, 50),
        ("BR", 1020, 1480, -180, 50),
        ("BE", 1720, 2000, -180, 50),
    ]

    safe_polys = []

    for name, xmin, xmax, ymin, ymax in blocks:
        # Divide each block into a 2x2 grid of candidate building footprints
        nx, ny = 2, 2
        dx = (xmax - xmin) / nx
        dy = (ymax - ymin) / ny

        for ix in range(nx):
            for iy in range(ny):
                bx1 = xmin + ix * dx + 15
                bx2 = xmin + (ix + 1) * dx - 15
                by1 = ymin + iy * dy + 15
                by2 = ymin + (iy + 1) * dy - 15

                candidate = [(bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2)]
                if is_strictly_safe(candidate, lanes, junctions, min_clearance=30.0):
                    b_id = f"bldg_{name}_{ix+1}_{iy+1}"
                    color = "0.99,0.99,0.99" if (ix + iy) % 2 == 0 else "0.94,0.94,0.96"
                    shape_str = f"{bx1:.1f},{by1:.1f} {bx2:.1f},{by1:.1f} {bx2:.1f},{by2:.1f} {bx1:.1f},{by2:.1f}"
                    safe_polys.append((b_id, "building", color, 2, shape_str))

    with open("multi_junction.add.xml", "w") as f:
        f.write("<additional>\n")
        for pid, ptype, color, layer, shape in safe_polys:
            f.write(f'    <poly id="{pid}" type="{ptype}" color="{color}" layer="{layer}" fill="true" shape="{shape}"/>\n')
        f.write("</additional>\n")

    print(f"Generated {len(safe_polys)} perfectly safe, verified buildings in multi_junction.add.xml.")

if __name__ == "__main__":
    generate()
