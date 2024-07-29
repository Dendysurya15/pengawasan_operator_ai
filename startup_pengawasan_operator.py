import os
import subprocess
import time
import signal
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('script.log'),
        logging.StreamHandler()
    ]
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_conda_path():
    try:
        conda_path = r'C:\ProgramData\anaconda3\Scripts\conda.exe'
        logging.info(f"Conda path found: {conda_path}")
        return conda_path
    except subprocess.CalledProcessError:
        logging.error("Conda not found in PATH.")
        return None

def activate_conda_env(env_name):
    conda_path = get_conda_path()
    if not conda_path:
        logging.error("Failed to find Conda executable.")
        return
    try:
        activate_cmd = f'"{conda_path}" activate {env_name}'
        subprocess.run(activate_cmd, shell=True, check=True)
        logging.info(f"The {env_name} environment is activated.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to activate environment {env_name}: {e}")

def open_directory(path):
    try:
        process = subprocess.Popen(['explorer', path])
        logging.info(f"Opened directory: {path}")
        return process
    except FileNotFoundError as e:
        logging.error(f"Failed to open directory {path}: {e}")
        return None

def close_directory(process):
    try:
        os.kill(process.pid, signal.SIGTERM)
        logging.info("Closed the opened directory.")
    except Exception as e:
        logging.error(f"Failed to close the directory: {e}")

def find_model_file(model_directory):
    for root, dirs, files in os.walk(model_directory):
        for file in files:
            if file.endswith('.pt') or file.endswith('.weights'):  # Adjust based on model file extensions
                logging.info(f"Model file found: {os.path.join(root, file)}")
                return os.path.join(root, file)
    logging.warning("Model file not found.")
    return None

def run_python_file(env_name, file_path, open_dir_process):
    conda_path = get_conda_path()
    if not conda_path:
        logging.error("Failed to find Conda executable.")
        return
    while True:
        try:
            run_cmd = f'"{conda_path}" run -n {env_name} python {file_path}'
            subprocess.run(run_cmd, shell=True, check=True)
            logging.info(f"Successfully ran the file: {file_path}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to run the file {file_path}: {e}")
        
        logging.info("Process closed. Restarting in 5 seconds...")
        time.sleep(5)

        # Close the opened directory
        # if open_dir_process:
        #     close_directory(open_dir_process)
        #     break

if _name_ == "_main_":
    # Define the base directory
    base_dir = r'C:\Users\User\Documents\yolov8ffb-db_sqlite'
    
    # Define directories and paths using the base directory
    open_dir = base_dir
    python_file_path = os.path.join(base_dir, 'operator_behaviour_save.py')
    logging.info(f"Python file path: {python_file_path}")

    # Activate conda environment
    env_name = 'yolov8'
    activate_conda_env(env_name)

    # Open directory
    open_dir_process = open_directory(open_dir)

    # Run the Python file with arguments
    run_python_file(env_name, python_file_path, open_dir_process)