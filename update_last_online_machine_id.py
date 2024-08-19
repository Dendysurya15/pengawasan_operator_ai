import argparse
import requests

def update_machine_id(machine_id):
    try:
        # URL of the PHP endpoint
        url = 'http://srs-ssms.com/op_monitoring/update_last_online.php'
        
        # Data to send in the request
        data = {'machine_id': machine_id}
        
        # Make the HTTP POST request
        response = requests.post(url, data=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            print(f"Last Online Machine ID {machine_id} updated successfully.")
        else:
            print(f"Failed to update last online machine ID {machine_id}. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error updating machine ID: {e}")

def main():
    parser = argparse.ArgumentParser(description="Update last online machine ID.")
    parser.add_argument("machine_id", type=int, help="ID of the machine to update")
    args = parser.parse_args()

    update_machine_id(args.machine_id)

if __name__ == "__main__":
    main()
