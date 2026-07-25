#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from explain_eat.recognition import recognize_food

# Test image recognition
print('=== Image Recognition Test ===')
print('Loading chicken image...')

try:
    items = recognize_food(image_path='explain_eat/training/images/chicken/chicken_01.jpg.jpg')
    print(f'Items detected: {len(items)} (should be 1 only)')
    print()
    
    for item in items:
        print(f'Food: {item.get("name")}')
        print(f'Grams: {item.get("grams", "?")}')
        print(f'Portion: {item.get("portion")}')
        print(f'Confidence: {item.get("confidence", "N/A")}')
        print()
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
