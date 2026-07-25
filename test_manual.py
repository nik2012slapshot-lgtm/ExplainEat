#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from explain_eat.recognition import recognize_food

# Test 1: Manual single item
print('=== Test 1: Manual Entry - Single Item ===')
items = recognize_food(manual_items=[{'name': 'Hähnchen', 'grams': 150}])
print(f'Items returned: {len(items)}')
for item in items:
    print(f'  - {item["name"]}: {item.get("grams", "?")}g ({item.get("portion")})')
print()

# Test 2: Manual multiple items  
print('=== Test 2: Manual Entry - Multiple Items ===')
items = recognize_food(manual_items=[
    {'name': 'Hähnchen', 'grams': 150},
    {'name': 'Reis', 'grams': 200},
    {'name': 'Broccoli', 'grams': 100}
])
print(f'Items returned: {len(items)}')
for item in items:
    print(f'  - {item["name"]}: {item.get("grams", "?")}g ({item.get("portion")})')
