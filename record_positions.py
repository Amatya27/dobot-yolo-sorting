# record_positions.py
import json, time, sys
try:
    import pydobot
    from pydobot.dobot import MODE_PTP
except Exception as e:
    raise SystemExit("pydobot not available: " + str(e))

def get_pose_dict(p):
    return {"x": float(p[0]), "y": float(p[1]), "z": float(p[2]), "r": float(p[3])}

def main(port="COM8"):
    dev = pydobot.Dobot(port=port)
    time.sleep(0.5)
    print("Connected to Dobot on", port)
    print("We will record these poses in order: HOME, PICK_UP (hover), PALLET_A_DROP, PALLET_B_DROP")
    positions = {}

    input("\n1) Ensure workspace clear. Place robot so you can HOME it. Press Enter to home now...")
    dev.home()
    time.sleep(2)
    pose, _ = dev.get_pose()
    positions["home"] = get_pose_dict(pose)
    print("Saved HOME:", positions["home"])

    input("\n2) Move robot above workspace center (hover position, ~100-120 mm above table). Press Enter when positioned...")
    pose, _ = dev.get_pose()
    positions["pick_up"] = get_pose_dict(pose)
    print("Saved PICK_UP (hover):", positions["pick_up"])

    input("\n3) Move robot above PALLET A drop zone. Press Enter when ready...")
    pose, _ = dev.get_pose()
    positions["pallet_a_drop"] = get_pose_dict(pose)
    print("Saved PALLET_A_DROP:", positions["pallet_a_drop"])

    input("\n4) Move robot above PALLET B drop zone. Press Enter when ready...")
    pose, _ = dev.get_pose()
    positions["pallet_b_drop"] = get_pose_dict(pose)
    print("Saved PALLET_B_DROP:", positions["pallet_b_drop"])

    fname = "positions.json"
    with open(fname, "w") as f:
        json.dump(positions, f, indent=2)
    print("\nAll poses saved to", fname)
    dev.close()

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv)>1 else "COM8"
    main(port)
