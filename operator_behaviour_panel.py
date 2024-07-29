import cv2
from ultralytics import YOLO
import time
import numpy as np
from collections import defaultdict

# Load a pretrained YOLOv8n model
model = YOLO("yolov8m.pt")

# IP camera URL with authentication
ip_camera_url = "rtsp://admin:SCM@2024@10.9.135.160/video"

# Initialize video capture
cap = cv2.VideoCapture(ip_camera_url)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# Initialize time variables for FPS calculation
prev_time = time.time()
fps = 0

# Function to draw rectangles with titles and detection text
def draw_rectangle(frame, rect, color=(0, 0, 255), title="", detection_text=""):
    points_list, title_text, color_value = rect
    points = np.array(points_list, dtype=np.int32)
    points = points.reshape((-1, 1, 2))
    
    cv2.polylines(frame, [points], isClosed=True, color=color_value, thickness=2)
    
    x, y = points_list[0]
    cv2.putText(frame, title_text, (x + 10, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color_value, 3, cv2.LINE_AA)
    
    if detection_text:
        cv2.putText(frame, detection_text, (x + 10, y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_value, 2, cv2.LINE_AA)

# Function to format seconds to hh:mm:ss
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

panel_induk = (
    ([0, 0], [700, 0], [700, 850], [0, 850]),
    "Panel induk engine room",
    (0, 0, 255)  # Red
)

panel_coords = panel_induk[0]

panel_x_min = min(coord[0] for coord in panel_coords)
panel_x_max = max(coord[0] for coord in panel_coords)
panel_y_min = min(coord[1] for coord in panel_coords)
panel_y_max = max(coord[1] for coord in panel_coords)

genset = (
    ([930, 0], [1400, 0], [1400, 190], [930, 190]),
    "Genset",
    (255, 0, 0)  # Blue
)

genset_coords = genset[0]

genset_x_min = min(coord[0] for coord in genset_coords)
genset_x_max = max(coord[0] for coord in genset_coords)
genset_y_min = min(coord[1] for coord in genset_coords)
genset_y_max = max(coord[1] for coord in genset_coords)

turbin_area = (
    ([930, 200], [1700, 200], [1700, 1000], [930, 1000]),
    "Turbin & Area Meja Kursi",
    (0, 255, 0)  # Green
)

turbin_coords = turbin_area[0]

turbin_x_min = min(coord[0] for coord in turbin_coords)
turbin_x_max = max(coord[0] for coord in turbin_coords)
turbin_y_min = min(coord[1] for coord in turbin_coords)
turbin_y_max = max(coord[1] for coord in turbin_coords)

# Create a window and set it to fullscreen
window_name = 'Pengawasan Operator Berbasis AI'
cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize dictionaries for duration tracking
areas = ['panel', 'genset', 'turbin', 'no_person']
cumulative_durations = {area: 0 for area in areas}

while True:
    # Read frame-by-frame from the IP camera
    ret, frame = cap.read()
   
    if not ret:
        print("Error: Failed to retrieve frame.")
        break

    # Start timing
    start_time = time.time()

    # Perform inference
    results = model.track(frame, classes=[0], imgsz=640, conf=0.08)

    # Initialize counters and flags
    panel_count = 0
    genset_count = 0
    turbin_count = 0
    person_detected = False

    current_time = time.time()
    elapsed_time = current_time - prev_time
    prev_time = current_time

    # Iterate through detected objects
    for result in results[0].boxes.data:
        result_list = result.tolist()
        x1, y1, x2, y2, conf, class_id = result_list[:6]
        
        if int(class_id) == 0:  # Class 0 is typically for persons
            person_detected = True
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            
            if center_y > turbin_y_min and center_y < turbin_y_max and center_x > turbin_x_min and center_x < turbin_x_max:
                area = 'turbin'
                turbin_count += 1
            elif center_y > panel_y_min and center_y < panel_y_max and center_x > panel_x_min and center_x < panel_x_max:
                area = 'panel'
                panel_count += 1
            elif center_y > genset_y_min and center_y < genset_y_max and center_x > genset_x_min and center_x < genset_x_max:
                area = 'genset'
                genset_count += 1
            else:
                area = None

            if area:
                cumulative_durations[area] += elapsed_time

    if not person_detected:
        cumulative_durations['no_person'] += elapsed_time

    # Prepare detection texts with cumulative durations
    panel_text = f"Persons: {panel_count}, Duration: {format_time(cumulative_durations['panel'])}"
    genset_text = f"Persons: {genset_count}, Duration: {format_time(cumulative_durations['genset'])}"
    turbin_text = f"Persons: {turbin_count}, Duration: {format_time(cumulative_durations['turbin'])}"

    # Draw results on the frame
    annotated_frame = results[0].plot()
    draw_rectangle(annotated_frame, panel_induk, panel_induk[2], panel_induk[1], panel_text)
    draw_rectangle(annotated_frame, genset, genset[2], genset[1], genset_text)
    draw_rectangle(annotated_frame, turbin_area, turbin_area[2], turbin_area[1], turbin_text)

    # Calculate FPS
    fps = 1 / elapsed_time if elapsed_time > 0 else 0

    height, width = annotated_frame.shape[:2]
    # Display FPS and No Person Duration on the frame
    cv2.putText(annotated_frame, f'FPS: {fps:.2f}', (10, height - 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(annotated_frame, f'No Person: {format_time(cumulative_durations["no_person"])}', (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Display the resulting frame
    cv2.imshow(window_name, annotated_frame)

    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
