# utils/__init__.py
# Пустой файл

# utils/storage.py
import json
import os
from typing import Dict, Any

def load_data(path: str) -> tuple[Dict[int, int], Dict[int, Dict[str, int]]]:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('partners', {}), data.get('messages', {})
    return {}, {}

def save_data(path: str, partners: Dict[int, int], messages: Dict[int, Dict[str, int]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {'partners': partners, 'messages': messages}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
