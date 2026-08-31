import traci
import time
import os

sumo_cmd = [
    "sumo-gui",
    "-c", "multi_junction.sumocfg",
    "--gui-settings-file", "gui-settings.cfg",
    "--start",
    "--quit-on-end",
    "--delay", "0"
]

print("Starting verification simulation with SUMO-GUI...")
traci.start(sumo_cmd)

# Set standard scheme
try:
    traci.gui.setSchema("View #0", "standard")
except Exception as e:
    print("Schema note:", e)

# Track vehicle types captured
captured_types = set()
types_to_find = {"car_silver", "car_red", "car_blue", "car_suv", "van_white", "city_bus", "coach_bus", "delivery_truck", "heavy_truck", "motorcycle"}

# Run 400 steps (40s simulation time)
for step in range(400):
    traci.simulationStep()
    vehs = traci.vehicle.getIDList()
    
    # Capture junction overview around step 150
    if step == 150:
        traci.gui.setOffset("View #0", 750.0, 500.0)
        traci.gui.setZoom("View #0", 500.0)
        time.sleep(0.1)
        traci.gui.screenshot("View #0", "multi_junction_traffic_stream.png")
        print("Captured multi_junction_traffic_stream.png")
        
    # Capture closeups of diverse vehicle types
    if step >= 100:
        for vid in vehs:
            vtype = traci.vehicle.getTypeID(vid)
            if vtype in types_to_find and vtype not in captured_types:
                x, y = traci.vehicle.getPosition(vid)
                traci.gui.setOffset("View #0", x, y)
                traci.gui.setZoom("View #0", 1400.0)
                time.sleep(0.1)
                filename = f"veh_{vtype}.png"
                traci.gui.screenshot("View #0", filename)
                captured_types.add(vtype)
                print(f"Captured {filename} at ({x:.1f}, {y:.1f})")

traci.close()
print(f"Verification complete! Captured types: {captured_types}")
