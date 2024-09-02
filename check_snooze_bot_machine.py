import argparse
import requests
import json

def check_snooze_bot(machine_id):
    try:
        url = 'http://srs-ssms.com/op_monitoring/check_snooze_time.php'
        data = {'machine_id': machine_id}
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                status = response_json.get('status', 'No status key found')
                print(json.dumps({'status': status}))  # Print as JSON
            except ValueError:
                print(json.dumps({'status': 'Error decoding JSON'}))
        else:
            print(json.dumps({'status': f'Failed with status code {response.status_code}'}))
    except Exception as e:
        print(json.dumps({'status': f'Error occurred: {e}'}))

def main():
    parser = argparse.ArgumentParser(description="Update last online machine ID.")
    parser.add_argument("machine_id", type=int, help="ID of the machine to update")
    args = parser.parse_args()
    check_snooze_bot(args.machine_id)

if __name__ == "__main__":
    main()
