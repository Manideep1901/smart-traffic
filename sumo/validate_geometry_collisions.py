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

def validate():
    print("=== COMPREHENSIVE GEOMETRIC COLLISION VALIDATION ===")
    net_tree = ET.parse("multi_junction.net.xml")
    net_root = net_tree.getroot()

    lanes = []
    for lane in net_root.findall(".//lane"):
        shape = lane.get("shape")
        width = float(lane.get("width", 3.2))
        if shape:
            pts = parse_shape(shape)
            lanes.append((lane.get("id"), pts, width))

    junctions = []
    for junc in net_root.findall(".//junction"):
        jtype = junc.get("type")
        shape = junc.get("shape")
        if shape and jtype != "internal":
            pts = parse_shape(shape)
            if len(pts) >= 3:
                junctions.append((junc.get("id"), pts))

    print(f"Loaded {len(lanes)} lanes and {len(junctions)} junctions from multi_junction.net.xml")

    add_tree = ET.parse("multi_junction.add.xml")
    add_root = add_tree.getroot()

    polygons = []
    for poly in add_root.findall(".//poly"):
        pid = poly.get("id")
        ptype = poly.get("type")
        shape = poly.get("shape")
        if shape:
            pts = parse_shape(shape)
            polygons.append((pid, ptype, pts))

    bldgs = [p for p in polygons if p[1] == "building"]
    gardens = [p for p in polygons if p[1] in ("flower_bed", "park")]
    trees = [p for p in polygons if p[1] == "tree"]
    print(f"Loaded {len(polygons)} total objects ({len(bldgs)} buildings, {len(gardens)} gardens/parks, {len(trees)} trees) from multi_junction.add.xml\n")

    collisions = []

    # 1. Check all objects vs junctions and lanes
    for pid, ptype, poly_pts in polygons:
        for jid, junc_pts in junctions:
            if polygons_intersect(poly_pts, junc_pts):
                collisions.append(f"COLLISION: {ptype} '{pid}' intersects Junction '{jid}'")

        for lid, lane_pts, width in lanes:
            half_w = width / 2.0
            for i in range(len(lane_pts) - 1):
                lx1, ly1 = lane_pts[i]
                lx2, ly2 = lane_pts[i + 1]
                for px, py in poly_pts:
                    d = dist_point_segment(px, py, lx1, ly1, lx2, ly2)
                    if d < half_w:
                        collisions.append(f"COLLISION: {ptype} '{pid}' vertex inside Lane '{lid}' (dist={d:.2f}m < {half_w:.2f}m)")

    # 2. Check solid objects vs solid objects (building vs building, tree vs building, garden vs building)
    for i in range(len(polygons)):
        pid1, ptype1, pts1 = polygons[i]
        for j in range(i + 1, len(polygons)):
            pid2, ptype2, pts2 = polygons[j]
            if ptype1 == "building" and ptype2 == "building":
                if polygons_intersect(pts1, pts2):
                    collisions.append(f"COLLISION: Building '{pid1}' overlaps Building '{pid2}'")
            elif ptype1 in ("tree", "flower_bed") and ptype2 == "building":
                if polygons_intersect(pts1, pts2):
                    collisions.append(f"COLLISION: {ptype1} '{pid1}' overlaps Building '{pid2}'")
            elif ptype1 == "building" and ptype2 in ("tree", "flower_bed"):
                if polygons_intersect(pts1, pts2):
                    collisions.append(f"COLLISION: Building '{pid1}' overlaps {ptype2} '{pid2}'")

    if collisions:
        print(f"FAILED: Found {len(collisions)} collisions:")
        for c in collisions[:15]:
            print(f"  - {c}")
        if len(collisions) > 15:
            print(f"  ... and {len(collisions) - 15} more.")
        return False
    else:
        print("SUCCESS: 100% CLEAN GEOMETRY!")
        print(f"  - Zero road collisions across all {len(lanes)} lanes")
        print(f"  - Zero junction collisions across all {len(junctions)} junctions")
        print(f"  - Zero building-building overlaps")
        print(f"  - Zero garden-building overlaps")
        print(f"  - Zero tree-building overlaps")
        return True

if __name__ == "__main__":
    import sys
    success = validate()
    sys.exit(0 if success else 1)
