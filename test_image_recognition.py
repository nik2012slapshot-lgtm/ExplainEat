#!/usr/bin/env python3
import requests
import os

# Test image recognition
chicken_image = r'explain_eat/training/images/chicken/chicken_01.jpg.jpg'

if os.path.exists(chicken_image):
    with open(chicken_image, 'rb') as f:
        files = {'image': f}
        data = {
            'age': 30,
            'weight': 70,
            'activity': 'moderate',
            'goal': 'health',
            'allergies': '[]'
        }
        response = requests.post('http://127.0.0.1:5000/analyze_image', files=files, data=data)
        result = response.json()
        
        print(f'✓ Success: {result.get("success")}')
        print(f'✓ Items detected: {len(result.get("detected_items", []))} (should be 1 only!)')
        print()
        
        for item in result.get('detected_items', []):
            print(f'  Food: {item["name"]}')
            print(f'  Grams: {item.get("grams", "?")}g')
            print(f'  Portion: {item.get("portion", "N/A")}')
            print(f'  Confidence: {item.get("confidence", "N/A")}')
            print()
else:
    print(f'Image not found: {chicken_image}')
