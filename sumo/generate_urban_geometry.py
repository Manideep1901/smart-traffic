import xml.etree.ElementTree as ET

def generate_add_xml():
    xml_content = """<additional>
    <!-- =================================================================== -->
    <!-- URBAN PARCELS (Bounded strictly inside urban blocks)                 -->
    <!-- =================================================================== -->

    <!-- BLOCK 1: Top-Left (West of Diagonal N1-J1, North of Highway W1-J1) -->
    <!-- Safe region: x in [-280, 320], y in [545, 850], y + x <= 860 -->
    <poly id="parcel_TL_depot" type="commercial" color="0.82,0.85,0.88" layer="0" fill="true"
          shape="-270,545 20,545 -100,840 -270,840"/>
    <poly id="depot_strip_1" type="commercial" color="0.70,0.74,0.78" layer="1" fill="true"
          shape="-250,570 0,570 -10,600 -250,600"/>
    <poly id="depot_strip_2" type="commercial" color="0.70,0.74,0.78" layer="1" fill="true"
          shape="-250,640 -40,640 -50,670 -250,670"/>
    <poly id="depot_strip_3" type="commercial" color="0.70,0.74,0.78" layer="1" fill="true"
          shape="-250,710 -80,710 -90,740 -250,740"/>
    <poly id="bldg_TL_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="50,545 270,545 150,670 50,670"/>
    <poly id="bldg_TL_2" type="building" color="0.94,0.94,0.96" layer="2" fill="true"
          shape="-50,695 120,695 50,770 -50,770"/>

    <!-- BLOCK 2: Top-Middle (East of Diagonal N1-J1, North of Highway J1-J2, West of N2-J2) -->
    <!-- Safe region: x in [450, 915], y in [545, 920], y + x >= 940 -->
    <poly id="parcel_TM" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="480,545 915,545 915,920 120,920 400,640"/>
    <poly id="bldg_TM_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="500,560 670,560 670,680 500,680"/>
    <poly id="bldg_TM_2" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="700,560 890,560 890,680 700,680"/>
    <poly id="bldg_TM_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="500,710 670,710 670,830 500,830"/>
    <poly id="bldg_TM_4" type="building" color="0.94,0.94,0.96" layer="2" fill="true"
          shape="700,710 890,710 890,830 700,830"/>
    <poly id="park_TM_green" type="park" color="0.18,0.50,0.22" layer="3" fill="true"
          shape="520,850 870,850 870,905 520,905"/>
    <poly id="lawn_TM_inner" type="park" color="0.45,0.75,0.48" layer="4" fill="true"
          shape="550,865 840,865 840,895 550,895"/>

    <!-- BLOCK 3: Top-Right (East of N2-J2, North of Highway J2-J3, West of Right Highway N3-J3) -->
    <!-- Safe region: x in [985, 1550], y in [545, 920] -->
    <poly id="parcel_TR" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="985,545 1550,545 1550,920 985,920"/>
    <poly id="bldg_TR_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1010,565 1250,565 1250,700 1010,700"/>
    <poly id="bldg_TR_2" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="1285,565 1525,565 1525,700 1285,700"/>
    <poly id="bldg_TR_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1010,730 1525,730 1525,900 1010,900"/>
    <poly id="bldg_TR_courtyard" type="residential" color="0.96,0.91,0.87" layer="3" fill="true"
          shape="1080,760 1455,760 1455,870 1080,870"/>

    <!-- BLOCK 4: Top-Far-East (East of Right Highway N3-J3, North of Highway J3-E1) -->
    <!-- Safe region: x in [1650, 2050], y in [545, 920] -->
    <poly id="parcel_TE" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="1650,545 2050,545 2050,920 1650,920"/>
    <poly id="bldg_TE_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1680,565 1840,565 1840,710 1680,710"/>
    <poly id="bldg_TE_2" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="1870,565 2020,565 2020,710 1870,710"/>
    <poly id="bldg_TE_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1680,740 2020,740 2020,890 1680,890"/>

    <!-- BLOCK 5: Middle-Left (South of Highway W1-J1, West of Local J1-J4, North of Local W2-J4) -->
    <!-- Safe region: x in [-280, 200], y in [185, 455] -->
    <poly id="parcel_ML" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="-270,185 200,185 270,340 330,455 -270,455"/>
    <poly id="bldg_ML_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="-250,205 -50,205 -50,310 -250,310"/>
    <poly id="bldg_ML_2" type="building" color="0.94,0.94,0.96" layer="2" fill="true"
          shape="-20,205 170,205 170,310 -20,310"/>
    <poly id="bldg_ML_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="-250,335 -50,335 -50,435 -250,435"/>
    <poly id="bldg_ML_4" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="-20,335 190,335 190,435 -20,435"/>

    <!-- BLOCK 6: Central Core (Between J1, J2, J4, J5) -->
    <!-- Safe region: x in [295, 860], y in [185, 455] -->
    <poly id="parcel_C" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="295,185 860,185 910,455 450,455"/>
    <poly id="bldg_C_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="340,205 560,205 560,305 340,305"/>
    <poly id="bldg_C_2" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="590,205 825,205 825,305 590,305"/>
    <poly id="bldg_C_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="480,335 660,335 660,435 480,435"/>
    <poly id="bldg_C_4" type="building" color="0.93,0.94,0.96" layer="2" fill="true"
          shape="690,335 870,335 870,435 690,435"/>
    <poly id="park_central" type="park" color="0.18,0.50,0.22" layer="3" fill="true"
          shape="340,335 450,335 450,435 340,435"/>

    <!-- BLOCK 7: Central-Right (Between J2, J3, J5, J6) -->
    <!-- Safe region: x in [940, 1550], y in [185, 455] -->
    <poly id="parcel_CR" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="940,185 1550,185 1550,455 985,455"/>
    <poly id="bldg_CR_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="970,205 1230,205 1230,305 970,305"/>
    <poly id="bldg_CR_2" type="building" color="0.94,0.94,0.96" layer="2" fill="true"
          shape="1265,205 1520,205 1520,305 1265,305"/>
    <poly id="bldg_CR_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1010,335 1230,335 1230,435 1010,435"/>
    <poly id="bldg_CR_4" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="1265,335 1520,335 1520,435 1265,435"/>

    <!-- BLOCK 8: Central-Far-East (East of Right Highway J3-J6) -->
    <!-- Safe region: x in [1650, 2050], y in [185, 455] -->
    <poly id="parcel_CE" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="1650,185 2050,185 2050,455 1650,455"/>
    <poly id="bldg_CE_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1680,205 1840,205 1840,310 1680,310"/>
    <poly id="bldg_CE_2" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="1870,205 2020,205 2020,310 1870,310"/>
    <poly id="bldg_CE_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1680,335 2020,335 2020,435 1680,435"/>

    <!-- BLOCK 9: Bottom-Left (South of Local W2-J4, West of Local J4-S1) -->
    <!-- Safe region: x in [-280, 215], y in [-230, 110] -->
    <poly id="parcel_BL" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="-270,-220 200,-220 200,105 -270,105"/>
    <poly id="bldg_BL_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="-250,-200 -50,-200 -50,-60 -250,-60"/>
    <poly id="bldg_BL_2" type="building" color="0.94,0.94,0.96" layer="2" fill="true"
          shape="-20,-200 170,-200 170,-60 -20,-60"/>
    <poly id="bldg_BL_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="-250,-30 -50,-30 -50,85 -250,85"/>
    <poly id="bldg_BL_4" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="-20,-30 170,-30 170,85 -20,85"/>

    <!-- BLOCK 10: Bottom-Middle (South of Local J4-J5, Between S1 and S2) -->
    <!-- Safe region: x in [285, 865], y in [-230, 110] -->
    <poly id="parcel_BM" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="290,-220 860,-220 860,105 290,105"/>
    <poly id="bldg_BM_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="320,-200 560,-200 560,-60 320,-60"/>
    <poly id="bldg_BM_2" type="building" color="0.94,0.94,0.96" layer="2" fill="true"
          shape="590,-200 830,-200 830,-60 590,-60"/>
    <poly id="bldg_BM_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="320,-30 560,-30 560,85 320,85"/>
    <poly id="bldg_BM_4" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="590,-30 830,-30 830,85 590,85"/>

    <!-- BLOCK 11: Bottom-Right (South of Local J5-J6, Between S2 and S3) -->
    <!-- Safe region: x in [935, 1550], y in [-230, 110] -->
    <poly id="parcel_BR" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="940,-220 1550,-220 1550,105 940,105"/>
    <poly id="bldg_BR_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="970,-200 1230,-200 1230,-60 970,-60"/>
    <poly id="bldg_BR_2" type="building" color="0.94,0.94,0.96" layer="2" fill="true"
          shape="1265,-200 1520,-200 1520,-60 1265,-60"/>
    <poly id="bldg_BR_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="970,-30 1230,-30 1230,85 970,85"/>
    <poly id="bldg_BR_4" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="1265,-30 1520,-30 1520,85 1265,85"/>

    <!-- BLOCK 12: Bottom-Far-East (South of Local J6-E2, East of Right Highway J6-S3) -->
    <!-- Safe region: x in [1650, 2050], y in [-230, 110] -->
    <poly id="parcel_BE" type="residential" color="0.96,0.91,0.87" layer="0" fill="true"
          shape="1650,-220 2050,-220 2050,105 1650,105"/>
    <poly id="bldg_BE_1" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1680,-200 1840,-200 1840,-60 1680,-60"/>
    <poly id="bldg_BE_2" type="building" color="0.95,0.95,0.97" layer="2" fill="true"
          shape="1870,-200 2020,-200 2020,-60 1870,-60"/>
    <poly id="bldg_BE_3" type="building" color="0.99,0.99,0.99" layer="2" fill="true"
          shape="1680,-30 2020,-30 2020,85 1680,85"/>

</additional>
"""
    with open("multi_junction.add.xml", "w") as f:
        f.write(xml_content.strip())
    print("Generated multi_junction.add.xml successfully.")

if __name__ == "__main__":
    generate_add_xml()
