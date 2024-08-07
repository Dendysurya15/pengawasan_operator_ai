import subprocess
import sys
import cv2
from ultralytics import YOLO
import time
import numpy as np
from dateutil import tz
import sqlite3
from datetime import datetime, date, timedelta
import json
import argparse
import os
import pusher

pusher_client = pusher.Pusher(app_id=u'1841216', key=u'b193dcd8922273835547', secret=u'5e39e309c9ee6a995b84', cluster=u'ap1')


def setup_database(script_dir):
    try:
        subprocess.run([sys.executable, os.path.join(script_dir, "setup_database.py")], check=True)
        print("Database setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running setup_database.py: {e}")
        sys.exit(1)

def format_time(seconds):
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

def get_existing_data():
    print(today_date, machine_id)
    cursor.execute('''
        SELECT uptime FROM pengawasan_operator
        WHERE date = ? AND machine_id = ?
    ''', (today_date, machine_id))
    result = cursor.fetchone()
    if result:
        return json.loads(result[0])
    return None

def draw_rectangle(frame, area):
    points = np.array(area['coords'], dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(frame, [points], isClosed=True, color=area['color'], thickness=2)
    x, y = area['coords'][0]
    cv2.putText(frame, area['title'], (x + 10, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, area['color'], 3, cv2.LINE_AA)
    detection_text = f"Persons: {area['count']}, Duration: {format_time(area['duration'])}"
    cv2.putText(frame, detection_text, (x + 10, y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, area['color'], 2, cv2.LINE_AA)

def get_machine_location(machine_id):

    cursor = conn.cursor()

    cursor.execute('''
        SELECT location FROM machine
        WHERE id = ?
    ''', (machine_id,))

    result = cursor.fetchone()
    

    if result:
        return result[0]
    else:
        return None
    
def save_to_database():
    uptime_data = [{"area": areas[area]['title'], "time": format_time(areas[area]['duration'])} for area in areas if area != 'No Person']
    uptime_data.append({"area": areas['No Person']['title'], "time": format_time(total_unattended_time)})
    uptime_json = json.dumps(uptime_data)

    cursor.execute('''
        UPDATE pengawasan_operator 
        SET uptime = ? 
        WHERE date = ? AND machine_id = ?
    ''', (uptime_json, today_date, machine_id))
    
    if cursor.rowcount == 0:
        cursor.execute('''
            INSERT INTO pengawasan_operator (date, machine_id, uptime)
            VALUES (?, ?, ?)
        ''', (today_date, machine_id, uptime_json))
    
    conn.commit()
    print(f"Data successfully updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def capture_screenshot(annotated_frame, screenshot_dir, compression_quality = 80):
    current_datetime = datetime.now()
    screenshot_folder = os.path.join(screenshot_dir, current_datetime.strftime("%Y_%m_%d"))
    os.makedirs(screenshot_folder, exist_ok=True)
    screenshot_filename = current_datetime.strftime("%Y_%m_%d_%H_%M_%S") + ".jpg"
    screenshot_path = os.path.join(screenshot_folder, screenshot_filename)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), compression_quality]
    _, encoded_frame = cv2.imencode('.jpg', annotated_frame, encode_param)

    # Save the compressed frame to disk
    with open(screenshot_path, 'wb') as f:
        f.write(encoded_frame)

    print(f"Screenshot saved: {screenshot_path}")
    return screenshot_filename

def hit_api_bot(fileName):

    jakarta_tz = tz.gettz('Asia/Jakarta')
    current_datetime = datetime.now(jakarta_tz)

    formatted_datetime = current_datetime.strftime("%A, %d %B %Y %H:%M")
    machine_location = get_machine_location(machine_id)
    if machine_location:
        pusher_client.trigger(u'operator-missing', u'python', {
            u'date': formatted_datetime,
            u'location': machine_location,
            u'fileName': fileName
        })
    else:
        print("Error: Could not retrieve machine location from the database.")
    # pusher_client.trigger(u'channel_trigger_bot_api', u'python', {u'some': u'love u'})
    
def main():
    parser = argparse.ArgumentParser(description="AI-based operator monitoring system.")
    default_directory = os.getcwd()
    parser.add_argument("--script_dir", type=str, default=default_directory, help="Directory containing setup_database.py")
    parser.add_argument("--machine_id", type=int, default=2, help="ID of the machine being monitored")
    parser.add_argument("--yolo-model", type=str, default="yolov8m-seg.pt", help="YOLO model file to use")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    parser.add_argument("--conf", type=float, default=0.9, help="Confidence threshold for object detection")
    args = parser.parse_args()
    
    setup_database(args.script_dir)

    global conn, cursor, model, today_date, machine_id, ip_camera_url, cap, areas, window_name, unattended_start_time, unattended_threshold, threshold_call_bot, total_unattended_time, unattended_watcher, existing_data, save_interval, last_save_time

    conn = sqlite3.connect('operator_behaviour.db')
    cursor = conn.cursor()

    model = YOLO(args.yolo_model)
    today_date = date.today().strftime("%Y-%m-%d")

    machine_id = args.machine_id
    print(machine_id)
    ip_camera_url = "rtsp://admin:SCM@2024@10.9.135.160/video"

    cap = cv2.VideoCapture(ip_camera_url)

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        exit()

    prev_time = time.time()
    fps = 0

    areas = {
        'Panel induk engine room': {
            'coords': ([0, 0], [700, 0], [700, 850], [0, 850]),
            'title': "Panel induk engine room",
            'color': (0, 0, 255),
            'count': 0,
            'duration': 0
        },
        'Genset': {
            'coords': ([930, 0], [1400, 0], [1400, 190], [930, 190]),
            'title': "Genset",
            'color': (255, 0, 0),
            'count': 0,
            'duration': 0
        },
        'Turbin & Area Meja Kursi': {
            'coords': ([930, 200], [1700, 200], [1700, 1000], [930, 1000]),
            'title': "Turbin & Area Meja Kursi",
            'color': (0, 255, 0),
            'count': 0,
            'duration': 0
        },
        'No Person': {
            'title': "No Person",
            'duration': 0
        }
    }

    for area in areas.values():
        if 'coords' in area:
            area['x_min'], area['x_max'] = min(coord[0] for coord in area['coords']), max(coord[0] for coord in area['coords'])
            area['y_min'], area['y_max'] = min(coord[1] for coord in area['coords']), max(coord[1] for coord in area['coords'])

    window_name = 'Pengawasan Operator Berbasis AI'
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    unattended_start_time = None
    unattended_threshold = 5  # seconds
    threshold_call_bot = timedelta(seconds=5)  
    total_unattended_time = 0
    unattended_watcher = 0
    existing_data = get_existing_data()
    print(existing_data)
    if existing_data:
        for area_data in existing_data:
            if area_data['area'] in areas:
                areas[area_data['area']]['duration'] = time_to_seconds(area_data['time'])

                if area_data['area'] == 'No Person':
                    total_unattended_time = time_to_seconds(area_data['time'])

    save_interval = timedelta(seconds=30, minutes=0)
    last_save_time = datetime.now()

    while True:
        ret, frame = cap.read()
       
        if not ret:
            print("Error: Failed to retrieve frame.")
            break

        start_time = time.time()
        results = model.predict(frame, classes=[0], imgsz=args.imgsz, conf=args.conf, verbose=False)

        person_detected = False
        current_time = datetime.now()
        elapsed_time = (current_time - datetime.fromtimestamp(prev_time)).total_seconds()
        prev_time = current_time.timestamp()

        for area in areas.values():
            if 'count' in area:
                area['count'] = 0

        detected_areas = set()  # Keep track of areas where objects are detected

        for result in results[0].boxes.data:
            x1, y1, x2, y2, conf, class_id = result.tolist()[:6]
            
            if int(class_id) == 0:
                person_detected = True
                center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
                
                for area_name, area in areas.items():
                    if 'coords' in area and (area['y_min'] < center_y < area['y_max'] and area['x_min'] < center_x < area['x_max']):
                        area['count'] += 1  # Increment the count for each bounding box in the area
                        detected_areas.add(area_name)
                        break

        if not person_detected:
            if unattended_start_time is None:
                unattended_start_time = current_time
            if (current_time - unattended_start_time).total_seconds() >= unattended_threshold:
                total_unattended_time += elapsed_time
                unattended_watcher += elapsed_time
                areas['No Person']['duration'] = total_unattended_time
                if unattended_watcher >= threshold_call_bot.total_seconds():

                    screenshot_dir = "screenshots"
                    compression_quality = 60
                    print('calling api bot')
                    file_name = capture_screenshot(annotated_frame, screenshot_dir , compression_quality)
                    hit_api_bot(file_name)
                    unattended_watcher = 0
        else:
            if unattended_start_time is not None:
                unattended_start_time = None
            unattended_watcher = 0
            areas['No Person']['duration'] = 0

        annotated_frame = results[0].plot()
        for area_name, area in areas.items():
            if 'coords' in area:    
                draw_rectangle(annotated_frame, area)

        fps = 1 / elapsed_time if elapsed_time > 0 else 0

        height, width = annotated_frame.shape[:2]
        cv2.putText(annotated_frame, f'FPS: {fps:.2f}', (10, height - 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(annotated_frame, f'No Person: {format_time(unattended_watcher)}', (10, height - 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(annotated_frame, f'Total Unattended: {format_time(total_unattended_time)}', (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(annotated_frame, f'imgsz: {args.imgsz}, conf: {args.conf}, model: {args.yolo_model}', (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.imshow(window_name, annotated_frame)

        if (current_time - last_save_time) >= save_interval:
            save_to_database()
            last_save_time = current_time

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    conn.close()

if __name__ == "__main__":
    main()
