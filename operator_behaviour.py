import cv2
from ultralytics import YOLO
import time
import numpy as np

# Load a pretrained YOLOv8n model
model = YOLO("yolov5nu.pt")

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

# Function to draw rectangles with titles
def draw_rectangle(frame, rect, color=(0, 0, 255), title="", elapsed_time=None):
    points_list, title_text, color_value = rect
    points = np.array(points_list, dtype=np.int32)
    points = points.reshape((-1, 1, 2))
    
    # Draw the rectangle outline on the frame
    cv2.polylines(frame, [points], isClosed=True, color=color_value, thickness=2)
    
    # Calculate the position to draw the title inside the rectangle
    x, y = points_list[0]
    cv2.putText(frame, title_text, (x + 10, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_value, 1, cv2.LINE_AA)
    
    if elapsed_time is not None:
        cv2.putText(frame, f'Time: {elapsed_time:.1f}s', (x + 10, y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_value, 1, cv2.LINE_AA)

def is_point_in_polygon(polygon, point):
    """Check if a point is inside a polygon"""
    point = tuple(map(int, point))  # Ensure point is a tuple with two integer values
    polygon = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(polygon, point, False) >= 0

def is_bbox_in_polygon(polygon, bbox):
    """Check if any point of the bounding box is inside the polygon"""
    # Convert bbox to list of points
    bbox_points = [
        (bbox[0][0], bbox[0][1]),  # Top-left
        (bbox[1][0], bbox[0][1]),  # Top-right
        (bbox[1][0], bbox[1][1]),  # Bottom-right
        (bbox[0][0], bbox[1][1])   # Bottom-left
    ]
    for point in bbox_points:
        if is_point_in_polygon(polygon, point):
            return True
    return False

# Define rectangles with an initial time of None
panel_induk = (
    ([0, 0], [700, 0], [700, 850], [0, 850]),
    "Panel induk engine room",
    (0, 0, 255),  # Red
    None  # Time when an object entered
)

genset = (
    ([930, 0], [1400, 0], [1400, 200], [930, 200]),
    "Genset",
    (255, 0, 0),  # Blue
    None  # Time when an object entered
)

turbin_area = (
    ([930, 200], [1700, 200], [1700, 1000], [930, 1000]),
    "Turbin & Area Meja Kursi",
    (0, 255, 0),  # Green
    None  # Time when an object entered
)

rectangles = [panel_induk, genset, turbin_area]

# Create a window and set it to fullscreen
window_name = 'Pengawasan Operator Berbasis AI'
cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
    # Read frame-by-frame from the IP camera
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to retrieve frame.")
        break

    # Start timing
    start_time = time.time()

    # Perform inference
    results = model.predict(frame, classes=[0], imgsz=1280, conf=0.1)

    # Draw results on the frame
    annotated_frame = results[0].plot()

    # Get bounding boxes
    bboxes = [result.boxes.xyxy.tolist() for result in results]
    for bbox in bboxes:
        bbox_points = [tuple(map(int, point)) for point in bbox]

        # Check if the detected object is within any of the rectangles
        for rect in rectangles:
            polygon = rect[0]
            if is_bbox_in_polygon(polygon, bbox_points):
                if rect[3] is None:
                    # Start counting the time when the object enters the rectangle
                    rect[3] = time.time()
            else:
                if rect[3] is not None:
                    # Stop counting if the object leaves the rectangle
                    rect[3] = None

    # Draw the rectangles and display elapsed time
    for rect in rectangles:
        draw_rectangle(annotated_frame, rect, rect[2], rect[1], 
                        elapsed_time=(time.time() - rect[3] if rect[3] is not None else None))

    # Calculate FPS
    current_time = time.time()
    elapsed_time = current_time - start_time
    fps = 1 / elapsed_time if elapsed_time > 0 else 0

    # Display FPS on the frame
    cv2.putText(annotated_frame, f'FPS: {fps:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Display the resulting frame
    cv2.imshow(window_name, annotated_frame)

    # Get the window dimensions
    x, y, window_width, window_height = cv2.getWindowImageRect(window_name)
    print(f"Window dimensions - Width: {window_width}, Height: {window_height}")

    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
