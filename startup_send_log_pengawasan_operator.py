import subprocess
import argparse
import os
import sys
import time

def run_send_log_script(script_dir):
    script_path = os.path.join(script_dir, "send_log_pengawasan_operator.py")
    
    while True:
        try:
            process = subprocess.Popen([sys.executable, script_path, "--script_dir", script_dir],
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
            process.wait()  # Wait for the process to complete

            # Check the return code to see if the script ran successfully
            if process.returncode == 0:
                print(f"Script '{script_path}' executed successfully.")
                break  # Exit loop if the script was successful
            else:
                print(f"Script '{script_path}' exited with error code {process.returncode}. Retrying...")

        except Exception as e:
            print(f"Error running '{script_path}': {e}")
        
        time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the database and run the send_log_pengawasan_operator script.")
    parser.add_argument("--script_dir", default=os.getcwd(), help="Directory containing the send_log_pengawasan_operator.py script (default: current working directory)")
    args = parser.parse_args()

    run_send_log_script(args.script_dir)
