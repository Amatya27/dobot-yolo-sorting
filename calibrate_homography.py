# calibrate_homography.py
import cv2, numpy as np, csv, time, sys
try:
    import pydobot
    from pydobot.dobot import MODE_PTP
except Exception:
    pydobot = None

def click_point(window, cap):
    clicked = {"pt":None}
    def onmouse(e,x,y,flags,param):
        if e == cv2.EVENT_LBUTTONDOWN:
            clicked["pt"] = (x,y)
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, onmouse)
    pt = None
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.putText(frame, "Left-click the calibration point. ESC to cancel.", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0),2)
        cv2.imshow(window, frame)
        key = cv2.waitKey(1) & 0xFF
        if clicked["pt"]:
            pt = clicked["pt"]; break
        if key == 27:
            break
    cv2.destroyWindow(window)
    return pt

def main(camera_index=0, port=None, n=6):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise SystemExit("Cannot open camera index " + str(camera_index))
    print("Camera opened. Calibration points:", n)
    img_pts = []; world_pts = []
    robot = None
    if port and pydobot:
        try:
            robot = pydobot.Dobot(port=port); time.sleep(0.5)
            print("Connected to robot for calibration on", port)
        except Exception as e:
            print("Robot connect failed:", e); robot = None

    for i in range(n):
        print(f"\nPoint {i+1}/{n}:")
        if robot:
            resp = input("Enter robot X,Y (mm) to move to or press ENTER if you will position it manually: ").strip()
            if resp:
                rx,ry = [float(s.strip()) for s in resp.split(",")]
                robot.move_to(mode=int(MODE_PTP.MOVJ_XYZ), x=rx, y=ry, z=120, r=0.0)
                time.sleep(1.0)
            else:
                input("Position robot manually then press Enter...")
            pose, _ = robot.get_pose()
            rx, ry = float(pose[0]), float(pose[1])
            print("Recorded robot XY:", rx, ry)
        else:
            resp = input("Enter robot X,Y (mm) for this calibration point: ")
            rx,ry = [float(s.strip()) for s in resp.split(",")]

        pt = click_point("Click calibration", cap)
        if pt is None:
            print("Cancelled"); cap.release(); return
        img_pts.append([pt[0], pt[1]])
        world_pts.append([rx, ry])
        print("Saved correspondence img",pt," -> robot",rx,ry)

    cap.release()
    img_pts = np.array(img_pts, dtype='float32')
    world_pts = np.array(world_pts, dtype='float32')
    H, mask = cv2.findHomography(img_pts, world_pts, method=0)
    np.save("homography.npy", H)
    with open("calib_points.csv","w",newline="") as f:
        writer = csv.writer(f); writer.writerow(["img_x","img_y","robot_x","robot_y"])
        for ip,wp in zip(img_pts, world_pts):
            writer.writerow([int(ip[0]), int(ip[1]), float(wp[0]), float(wp[1])])
    print("Saved homography.npy and calib_points.csv")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--port", type=str, default=None)
    p.add_argument("--n", type=int, default=6)
    args = p.parse_args()
    main(args.camera, args.port, args.n)
