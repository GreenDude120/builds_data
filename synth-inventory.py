import json
import hashlib
import os

def synth_item_id(item):
    base = item.get('base_type', '') + '|' + item.get('title', '')
    props = '|'.join(sorted(item.get('properties', [])))
    synth_from = '|'.join(sorted(item.get('synthesised_from', []))) if item.get('synthesised_from') else ''
    key = base + '|' + props + '|' + synth_from
    return hashlib.sha256(key.encode()).hexdigest()

def extract_synth_items(char, location):
    items = []
    for item in char.get(location, []) or []:
        tag = (item.get('Tag', '') + item.get('TextTag', '')).lower()
        if 'synthesized' in tag:
            items.append({
                'id': None,  # to be filled later
                'friendly_id': None,  # to be filled later
                'owner': char.get('Name', ''),
                'base_type': item.get('Tag', ''),
                'title': item.get('Title', ''),
                'properties': item.get('PropertyList', []),
                'synthesised_from': item.get('SynthesisedFrom', []),
                'location': location
            })
    return items

def main():
    synth_items = []
    seen_ids = set()

    # Load existing synth_inventory.json if it exists
    if os.path.exists('synth_inventory.json'):
        with open('synth_inventory.json', 'r') as f:
            try:
                synth_items = json.load(f)
                seen_ids = set(item['id'] for item in synth_items)
            except Exception:
                synth_items = []
                seen_ids = set()

    with open('hc_ladder.json', 'r') as f:
        data = json.load(f)

    new_items = []
    for char in data:
        for loc in ['Equipped', 'Inventory', 'MercenaryEquipped']:
            for item in extract_synth_items(char, loc):
                item_id = synth_item_id(item)
                if item_id not in seen_ids:
                    item['id'] = item_id
                    new_items.append(item)
                    seen_ids.add(item_id)

    synth_items.extend(new_items)

    # Assign friendly_id as a simple count (1-based)
    for idx, item in enumerate(synth_items, 1):
        item['friendly_id'] = idx

    with open('synth_inventory.json', 'w') as f:
        json.dump(synth_items, f, indent=2)

if __name__ == '__main__':
    main()