import xml.etree.ElementTree as ET

def generate_clean_city():
    # Base background plane for a clean modern urban map look
    polys = [
        # City ground base plane (layer -10)
        ("city_base_ground", "landuse", "0.90,0.92,0.90", -10, "-400,-350 2200,-350 2200,1050 -400,1050")
    ]

    # Clean building blocks clearly placed INSIDE the 12 non-conflicting zones
    # (x1, y1, width, height, type, color)
    buildings = [
        # --- ROW 1: TOP (y > 550) ---
        # Zone 1 (Top-Left depot area, x <= 0)
        ("bldg_TL_1", -220, 600, 80, 70, "commercial", "0.82,0.85,0.88"),
        ("bldg_TL_2", -120, 600, 70, 70, "commercial", "0.78,0.82,0.86"),
        ("bldg_TL_3", -220, 700, 80, 80, "building", "0.98,0.98,0.98"),
        ("bldg_TL_4", -120, 700, 70, 80, "building", "0.94,0.94,0.96"),

        # Zone 2 (Top-Middle-Left, 520 <= x <= 850, 580 <= y <= 880)
        ("bldg_TM_1", 520, 580, 140, 120, "building", "0.99,0.99,0.99"),
        ("bldg_TM_2", 700, 580, 140, 120, "building", "0.94,0.94,0.96"),
        ("bldg_TM_3", 520, 730, 140, 120, "building", "0.95,0.95,0.97"),
        ("bldg_TM_4", 700, 730, 140, 120, "building", "0.99,0.99,0.99"),
        ("park_TM", 550, 860, 260, 30, "park", "0.35,0.65,0.38"),

        # Zone 3 (Top-Middle-Right, 1020 <= x <= 1500, 580 <= y <= 880)
        ("bldg_TR_1", 1020, 580, 200, 120, "building", "0.99,0.99,0.99"),
        ("bldg_TR_2", 1260, 580, 200, 120, "building", "0.94,0.94,0.96"),
        ("bldg_TR_3", 1020, 730, 200, 120, "building", "0.95,0.95,0.97"),
        ("bldg_TR_4", 1260, 730, 200, 120, "building", "0.99,0.99,0.99"),

        # Zone 4 (Top-Right, 1680 <= x <= 2050, 580 <= y <= 880)
        ("bldg_TE_1", 1680, 580, 150, 120, "building", "0.99,0.99,0.99"),
        ("bldg_TE_2", 1860, 580, 150, 120, "building", "0.94,0.94,0.96"),
        ("bldg_TE_3", 1680, 730, 330, 120, "building", "0.98,0.98,0.98"),

        # --- ROW 2: MIDDLE (200 <= y <= 450) ---
        # Zone 5 (Middle-Left, x <= 150)
        ("bldg_ML_1", -220, 220, 150, 90, "building", "0.99,0.99,0.99"),
        ("bldg_ML_2", -40, 220, 160, 90, "building", "0.94,0.94,0.96"),
        ("bldg_ML_3", -220, 340, 150, 90, "building", "0.95,0.95,0.97"),
        ("bldg_ML_4", -40, 340, 160, 90, "building", "0.99,0.99,0.99"),

        # Zone 6 (Center Core, 480 <= x <= 830, 220 <= y <= 430)
        ("bldg_CM_1", 480, 220, 150, 90, "building", "0.99,0.99,0.99"),
        ("bldg_CM_2", 660, 220, 150, 90, "building", "0.94,0.94,0.96"),
        ("bldg_CM_3", 520, 340, 140, 90, "building", "0.95,0.95,0.97"),
        ("bldg_CM_4", 680, 340, 140, 90, "building", "0.99,0.99,0.99"),
        ("park_CM", 480, 340, 30, 90, "park", "0.35,0.65,0.38"),

        # Zone 7 (Center-Right, 1020 <= x <= 1500, 220 <= y <= 430)
        ("bldg_CR_1", 1020, 220, 200, 90, "building", "0.99,0.99,0.99"),
        ("bldg_CR_2", 1260, 220, 200, 90, "building", "0.94,0.94,0.96"),
        ("bldg_CR_3", 1020, 340, 200, 90, "building", "0.95,0.95,0.97"),
        ("bldg_CR_4", 1260, 340, 200, 90, "building", "0.99,0.99,0.99"),

        # Zone 8 (Center Far-East, 1680 <= x <= 2050, 220 <= y <= 430)
        ("bldg_CE_1", 1680, 220, 150, 90, "building", "0.99,0.99,0.99"),
        ("bldg_CE_2", 1860, 220, 150, 90, "building", "0.94,0.94,0.96"),
        ("bldg_CE_3", 1680, 340, 330, 90, "building", "0.98,0.98,0.98"),

        # --- ROW 3: BOTTOM (-220 <= y <= 80) ---
        # Zone 9 (Bottom-Left, -220 <= x <= 150, road is at x=250)
        ("bldg_BL_1", -220, -180, 150, 100, "building", "0.99,0.99,0.99"),
        ("bldg_BL_2", -40, -180, 160, 100, "building", "0.94,0.94,0.96"),
        ("bldg_BL_3", -220, -50, 150, 100, "building", "0.95,0.95,0.97"),
        ("bldg_BL_4", -40, -50, 160, 100, "building", "0.99,0.99,0.99"),

        # Zone 10 (Bottom-Center, 320 <= x <= 820, roads are at x=250 and x=900)
        ("bldg_BM_1", 330, -180, 220, 100, "building", "0.99,0.99,0.99"),
        ("bldg_BM_2", 580, -180, 220, 100, "building", "0.94,0.94,0.96"),
        ("bldg_BM_3", 330, -50, 220, 100, "building", "0.95,0.95,0.97"),
        ("bldg_BM_4", 580, -50, 220, 100, "building", "0.99,0.99,0.99"),

        # Zone 11 (Bottom-Right, 980 <= x <= 1500, roads are at x=900 and x=1600)
        ("bldg_BR_1", 980, -180, 220, 100, "building", "0.99,0.99,0.99"),
        ("bldg_BR_2", 1240, -180, 220, 100, "building", "0.94,0.94,0.96"),
        ("bldg_BR_3", 980, -50, 220, 100, "building", "0.95,0.95,0.97"),
        ("bldg_BR_4", 1240, -50, 220, 100, "building", "0.99,0.99,0.99"),

        # Zone 12 (Bottom Far-East, 1680 <= x <= 2050, road is at x=1600)
        ("bldg_BE_1", 1680, -180, 150, 100, "building", "0.99,0.99,0.99"),
        ("bldg_BE_2", 1860, -180, 150, 100, "building", "0.94,0.94,0.96"),
        ("bldg_BE_3", 1680, -50, 330, 100, "building", "0.98,0.98,0.98"),
    ]

    for bid, x, y, w, h, btype, color in buildings:
        shape_str = f"{x},{y} {x+w},{y} {x+w},{y+h} {x},{y+h}"
        layer = 1 if btype == "park" else 2
        polys.append((bid, btype, color, layer, shape_str))

    with open("multi_junction.add.xml", "w") as f:
        f.write("<additional>\n")
        for pid, ptype, color, layer, shape in polys:
            f.write(f'    <poly id="{pid}" type="{ptype}" color="{color}" layer="{layer}" fill="true" shape="{shape}"/>\n')
        f.write("</additional>\n")

    print(f"Generated {len(polys)} perfectly aligned urban polygons.")

if __name__ == "__main__":
    generate_clean_city()
