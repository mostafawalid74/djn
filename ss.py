"""
Saves a series of snapshots with the current camera as:
snapshot_<width>_<height>_<nnn>.jpg

Arguments:
    --folder    Output folder
    --name      File name
    --dwidth    Camera width
    --dheight   Camera height
    --raspi     Raspberry Pi camera mode
    --csi       Jetson Nano CSI camera mode
    --device    Camera device or CSI sensor ID
    --auto      Number of automatic snapshots
    --interval  Seconds between automatic snapshots

Buttons:
    q           - quit
    space bar   - save snapshot
"""

import cv2
import time
import sys
import argparse
import os

__author__ = "Tiziano Fiorenzani"
__date__ = "01/06/2018"


# Jetson Nano CSI camera pipeline
def gstreamer_pipeline(width, height, sensor_id=0):

    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), "
        f"width=(int){width}, height=(int){height}, "
        "format=(string)NV12, framerate=(fraction)30/1 ! "
        "nvvidconv flip-method=0 ! "
        "video/x-raw, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! "
        "appsink drop=true max-buffers=1 sync=false"
    )


def save_snaps(width=0, height=0, name="snapshot",
               folder=".", raspi=False, csi=False,
               device=0, auto=0, interval=3):

    if raspi:
        os.system('sudo modprobe bcm2835-v4l2')

    # ----------- OPEN CAMERA -----------------

    if csi:

        # Default resolution for CSI
        if width <= 0:
            width = 1920

        if height <= 0:
            height = 1080

        pipeline = gstreamer_pipeline(
            width, height, sensor_id=device
        )

        print("Opening Jetson Nano CSI camera")

        cap = cv2.VideoCapture(
            pipeline, cv2.CAP_GSTREAMER
        )

    else:

        cap = cv2.VideoCapture(device)

        if width > 0 and height > 0:
            print("Setting custom Width and Height")

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # ----------- CHECK CAMERA -----------------

    if not cap.isOpened():
        print("ERROR: Failed to open camera")
        cap.release()
        return

    print("Camera opened successfully")

    # ----------- CREATE FOLDER -----------------

    os.makedirs(folder, exist_ok=True)

    nSnap = 0

    print("Press SPACE to save a snapshot")
    print("Press Q to quit")

    if auto > 0:
        print("Automatic capture enabled")
        print("Number of snapshots:", auto)

    next_capture = time.monotonic() + interval

    try:

        while True:

            ret, frame = cap.read()

            # Check frame before imshow
            if not ret or frame is None or frame.size == 0:

                print("ERROR: Failed to read camera frame")
                break

            h, w = frame.shape[:2]

            # ----------- CAMERA PREVIEW -----------------

            if auto == 0:

                try:
                    cv2.imshow('camera', frame)
                    key = cv2.waitKey(1) & 0xFF

                except cv2.error as error:
                    print("OpenCV GUI error:", error)
                    print("Try --auto 20 to capture without GUI")
                    break

                if key == ord('q'):
                    break

                if key != ord(' '):
                    continue

            else:

                # Automatic capture mode without imshow
                if time.monotonic() < next_capture:
                    continue

            # ----------- SAVE SNAPSHOT -----------------

            while True:
                fileName = os.path.join(
                    folder,
                    "%s_%d_%d_%03d.jpg" %
                    (name, w, h, nSnap)
                )

                if not os.path.exists(fileName):
                    break

                nSnap += 1

            print("Saving image", nSnap)

            success = cv2.imwrite(fileName, frame)

            if success:
                print("Saved:", fileName)
            else:
                print("ERROR: Failed to save image")
                break

            nSnap += 1

            # ----------- AUTOMATIC MODE -----------------

            if auto > 0:

                if nSnap >= auto:
                    break

                next_capture = time.monotonic() + interval

    except KeyboardInterrupt:
        print("Capture stopped")

    finally:

        cap.release()

        if auto == 0:
            try:
                cv2.destroyAllWindows()
            except cv2.error:
                pass

    print("Files saved")


def main():

    # ---- DEFAULT VALUES ---
    SAVE_FOLDER = "."
    FILE_NAME = "snapshot"
    FRAME_WIDTH = 0
    FRAME_HEIGHT = 0

    # ----------- PARSE INPUTS -----------------

    parser = argparse.ArgumentParser(
        description="Save snapshots from camera"
    )

    parser.add_argument(
        "--folder",
        default=SAVE_FOLDER,
        help="Path to save folder"
    )

    parser.add_argument(
        "--name",
        default=FILE_NAME,
        help="Picture file name"
    )

    parser.add_argument(
        "--dwidth",
        default=FRAME_WIDTH,
        type=int,
        help="Camera width"
    )

    parser.add_argument(
        "--dheight",
        default=FRAME_HEIGHT,
        type=int,
        help="Camera height"
    )

    parser.add_argument(
        "--raspi",
        action="store_true",
        help="Use Raspberry Pi camera"
    )

    parser.add_argument(
        "--csi",
        action="store_true",
        help="Use Jetson Nano CSI camera"
    )

    parser.add_argument(
        "--device",
        default=0,
        type=int,
        help="Camera device ID or CSI sensor ID"
    )

    parser.add_argument(
        "--auto",
        default=0,
        type=int,
        help="Number of automatic snapshots"
    )

    parser.add_argument(
        "--interval",
        default=3,
        type=float,
        help="Seconds between automatic snapshots"
    )

    args = parser.parse_args()

    save_snaps(
        width=args.dwidth,
        height=args.dheight,
        name=args.name,
        folder=args.folder,
        raspi=args.raspi,
        csi=args.csi,
        device=args.device,
        auto=args.auto,
        interval=args.interval
    )

    print("Finished")


if __name__ == "__main__":
    main()
