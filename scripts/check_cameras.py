import cv2
import time

print('Checking camera indices 0..7')
for i in range(8):
    try:
        # Use CAP_DSHOW on Windows for more stable detection
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    except Exception as e:
        print(f'Index {i}: error while opening: {e}')
        continue
    time.sleep(0.4)
    opened = cap.isOpened() if cap is not None else False
    print(f'Index {i}: {"OPEN" if opened else "closed"}')
    if opened:
        ret, frame = cap.read()
        print(f'  read success: {ret}, frame type: {type(frame)}, shape: {None if frame is None else getattr(frame, "shape", None)}')
    try:
        if cap is not None:
            cap.release()
    except Exception:
        pass
print('Done')
