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
    return screenshot_filename, screenshot_path

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

def send_screenshot(screenshot_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    send_screenshot_script = os.path.join(script_dir, "send_screenshot_pengawasan_operator.py")

    try:
        subprocess.run([sys.executable, send_screenshot_script, "--file", screenshot_path], check=True)
        print("Screenshot sent successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error sending screenshot: {e}")


def is_box_in_area(box, area_points):
    """
    Check if a bounding box (x_min, y_min, x_max, y_max) is inside a polygon area.
    """
    x_min, y_min, x_max, y_max = box
    box_center = ((x_min + x_max) / 2, (y_min + y_max) / 2)
    
    # Use cv2.pointPolygonTest to determine if the box center is inside the polygon
    result = cv2.pointPolygonTest(np.array(area_points), box_center, False)
    
    return result >= 0  # If result is 1 or 0, the point is inside or on the edge of the polygon
 
def main():
    parser = argparse.ArgumentParser(description="AI-based operator monitoring system.")
    default_directory = os.getcwd()
    parser.add_argument("--script_dir", type=str, default=default_directory, help="Directory containing setup_database.py")
    parser.add_argument("--machine_id", type=int, default=2, help="ID of the machine being monitored")
    parser.add_argument("--yolo-model", type=str, default="yolov8m.pt", help="YOLO model file to use")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    parser.add_argument("--conf", type=float, default=0.1, help="Confidence threshold for object detection")
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

    # ex_areas = [
    #     {"name": "Area 1", "points":  [730, 300], [1500, 300], [1500, 1200], [230, 900]}  # Example rectangle
    #     # Add more areas as needed
    # ]

    for area in areas.values():
        if 'coords' in area:
            area['x_min'], area['x_max'] = min(coord[0] for coord in area['coords']), max(coord[0] for coord in area['coords'])
            area['y_min'], area['y_max'] = min(coord[1] for coord in area['coords']), max(coord[1] for coord in area['coords'])

    window_name = 'Pengawasan Operator Berbasis AI'
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    unattended_start_time = None
    unattended_threshold = 5  # seconds
    threshold_call_bot = timedelta(minutes=15)  
    total_unattended_time = 0
    unattended_watcher = 0
    existing_data = get_existing_data()
    
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
        class_names = model.names  # This returns a list of class names

        person_detected = False
        current_time = datetime.now()
        elapsed_time = (current_time - datetime.fromtimestamp(prev_time)).total_seconds()
        prev_time = current_time.timestamp()

        for area in areas.values():
            if 'count' in area:
                area['count'] = 0

        detected_areas = set()  # Keep track of areas where objects are detected

        color = (0,255,0)

        for result in results[0].boxes.data:
            x1, y1, x2, y2, conf, class_id = result.tolist()[:6]

            # print(str(result.tolist()))
            
            if int(class_id) == 0:
                person_detected = True
                center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)

                # exclude_detection = False
                # for ex_area in ex_areas:
                #     if is_box_in_area((x_min, y_min, x_max, y_max), area["points"]):
                #         exclude_detection = True
                #         break
                
                # if exclude_detection:
                #     continue  # Skip this detection if it's in an excluded area
                
                for area_name, area in areas.items():
                    if 'coords' in area and (area['y_min'] < center_y < area['y_max'] and area['x_min'] < center_x < area['x_max']):
                        area['count'] += 1
                        area['duration'] += elapsed_time
                        detected_areas.add(area_name)
                        break
            #####
            p1 = (int(x1), int(y1))  # top-left corner
            p2 = (int(x2), int(y2))  # bottom-right corner  
            cv2.rectangle(frame, p1, p2, color, thickness=1, lineType=cv2.LINE_AA)

            # Adjust text parameters
            label = f"{class_names[class_id]} {conf:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1
            font_thickness = 2
            
            # Get text size
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
            
            # Calculate background rectangle dimensions
            padding = 0
            bg_width = text_width + 2 * padding
            bg_height = text_height + 2 * padding

            # Calculate background rectangle coordinates
            bg_left = p1[0]
            bg_top = p1[1] - bg_height - 1 if p1[1] - bg_height - 1 > 0 else p1[1]
            bg_right = bg_left + bg_width
            bg_bottom = bg_top + bg_height

            # Draw background rectangle
            cv2.rectangle(frame, (bg_left, bg_top-15), (bg_right, bg_bottom), color, -1, cv2.LINE_AA)

            # Calculate text position
            text_left = bg_left + padding
            text_bottom = bg_bottom - padding - baseline

            # Draw text
            cv2.putText(
                frame,
                label,
                (text_left, text_bottom),
                font,
                font_scale,
                (255, 255, 255),
                font_thickness,
                lineType=cv2.LINE_AA,
            )
            #####
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
                    file_name, screenshot_path = capture_screenshot(annotated_frame, screenshot_dir, compression_quality)
                    send_screenshot(screenshot_path)
                    time.sleep(1.5) 
                    hit_api_bot(file_name)
                    unattended_watcher = 0
        else:
            if unattended_start_time is not None:
                unattended_start_time = None
            unattended_watcher = 0
            areas['No Person']['duration'] = 0

        annotated_frame = frame
        for area_name, area in areas.items():
            if 'coords' in area:    
                draw_rectangle(annotated_frame, area)

        # for ex_area in ex_areas:
        #     draw_rectangle(annotated_frame, ex_area)

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
