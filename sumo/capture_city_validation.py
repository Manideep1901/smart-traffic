import traci
import time

sumo_cmd = [
    "sumo-gui",
    "-c", "multi_junction.sumocfg",
    "--gui-settings-file", "gui-settings.cfg",
    "--start",
    "--quit-on-end",
    "--delay", "0"
]

print("Starting simulation to capture full visual city validation...")
traci.start(sumo_cmd)
try:
    traci.gui.setSchema("View #0", "standard")
except Exception:
    pass

for step in range(350):
    traci.simulationStep()
    
    # 1. Full city network overview with buildings, gardens, trees, traffic
    if step == 200:
        traci.gui.setOffset("View #0", 1200.0, 600.0)
        traci.gui.setZoom("View #0", 75.0)
        time.sleep(0.2)
        traci.gui.screenshot("View #0", "city_full_overview.png")
        print("Captured city_full_overview.png")
        
    # 2. North-West sector: residential & hillside flower garden park
    if step == 230:
        traci.gui.setOffset("View #0", 350.0, 950.0)
        traci.gui.setZoom("View #0", 350.0)
        time.sleep(0.2)
        traci.gui.screenshot("View #0", "city_sector_northwest_gardens.png")
        print("Captured city_sector_northwest_gardens.png")
        
    # 3. South-Central sector: grand botanical gardens, tree promenade & residential towers
    if step == 260:
        traci.gui.setOffset("View #0", 900.0, 250.0)
        traci.gui.setZoom("View #0", 350.0)
        time.sleep(0.2)
        traci.gui.screenshot("View #0", "city_sector_botanical_gardens.png")
        print("Captured city_sector_botanical_gardens.png")

    # 4. Central Highway J1-J2 Corridor with multi-class vehicles, signals, tech plaza
    if step == 290:
        traci.gui.setOffset("View #0", 950.0, 600.0)
        traci.gui.setZoom("View #0", 400.0)
        time.sleep(0.2)
        traci.gui.screenshot("View #0", "city_central_highway_traffic.png")
        print("Captured city_central_highway_traffic.png")

traci.close()
print("All visual validation screenshots captured!")
