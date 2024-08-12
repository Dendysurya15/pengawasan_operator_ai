import subprocess
import sys
import os
import argparse
import time

def run_operator_behaviour(script_dir, machine_id, yolo_model):
    operator_behaviour_script = os.path.join(script_dir, "operator_behaviour_save.py")
    while True:
        try:
            subprocess.run([
                sys.executable,
                operator_behaviour_script,
                "--script_dir", script_dir,
                "--machine_id", str(machine_id),
                "--yolo-model", yolo_model
            ], check=True)
        except subprocess.CalledProcessError:
            print("operator_behaviour_save.py error. Restarting in 5 seconds...")
        print("operator_behaviour_save.py closed. Restarting in 5 seconds...")
        time.sleep(5)

def main():
    parser = argparse.ArgumentParser(description="Startup script for operator monitoring system.")
    parser.add_argument("--script_dir", type=str, default=os.getcwd(), help="Directory containing setup_database.py")
    parser.add_argument("--machine_id", type=int, default=1, help="ID of the machine being monitored")
    parser.add_argument("--yolo-model", type=str, default="yolov8m.pt", help="YOLO model file to use")
    args = parser.parse_args()

    run_operator_behaviour(args.script_dir, args.machine_id, args.yolo_model)

if __name__ == "__main__":
    main()
