import subprocess
import argparse
import os
import sys

def run_send_log_script(script_dir):
    script_path = os.path.join(script_dir, "send_log_pengawasan_operator.py")
    try:
        subprocess.run([sys.executable, script_path], check=True)
        print(f"Script '{script_path}' executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running '{script_path}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the database and run the send_log_pengawasan_operator script.")
    parser.add_argument("--script_dir", default=os.getcwd(), help="Directory containing the send_log_pengawasan_operator.py script (default: current working directory)")
    args = parser.parse_args()

    run_send_log_script(args.script_dir)
