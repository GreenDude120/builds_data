#!/usr/bin/env python3
"""
Updated CSV handler for unified format supporting both character data and server metrics
"""

import csv
import json
from collections import defaultdict
from datetime import datetime

def update_unified_csv_from_character_data(characters, league, snapshot_label):
    """
    Update character skill/item data in unified CSV
    
    characters: list of character dicts from API
    league: 'SC' or 'HC' 
    snapshot_label: string like 'November' or 'Week_1'
    """
    csv_path = 'unified-usage-over-time.csv'
    
    # Load existing CSV
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Add new snapshot column if needed
    if snapshot_label not in fieldnames:
        fieldnames = list(fieldnames) + [snapshot_label]
        for row in rows:
            row[snapshot_label] = '0'
    
    # Create lookup for efficient updates
    row_lookup = {}
    for i, row in enumerate(rows):
        key = (row['Type'], row['League'], row['Class'], row['Name'])
        row_lookup[key] = i
    
    # Count character usage
    usage_counter = defaultdict(lambda: [0, 0])  # [normal, synth]
    
    for char in characters:
        cls = char.get("Class")
        
        # Count skills
        for tab in char.get("SkillTabs", []):
            for skill in tab.get("Skills", []):
                key = (skill["Name"], cls, "Skill", league)
                usage_counter[key][0] += skill["Level"]
        
        # Count equipped items
        for item in char.get("Equipped", []):
            quality_code = item.get("QualityCode")
            name = item.get("Title")
            if not name:
                continue
            
            if quality_code == "q_runeword":
                key = (name, "", "Runeword", league)
            elif quality_code == "q_set":
                key = (name, "", "Set", league)
            elif quality_code == "q_unique":
                key = (name, "", "Unique", league)
            else:
                continue
            
            is_synth = "Synthesized" in item.get("Tag", "")
            usage_counter[key][1 if is_synth else 0] += 1
        
        # Count mercenary items
        for item in char.get("MercenaryEquipped", []):
            quality_code = item.get("QualityCode")
            name = item.get("Title")
            if not name:
                continue
            
            if quality_code == "q_runeword":
                key = (name, "", "Mercenary Runeword", league)
            elif quality_code == "q_set":
                key = (name, "", "Mercenary Set", league)
            elif quality_code == "q_unique":
                key = (name, "", "Mercenary Unique", league)
            else:
                continue
            
            is_synth = "Synthesized" in item.get("Tag", "")
            usage_counter[key][1 if is_synth else 0] += 1
    
    # Update existing rows or create new ones
    for (name, cls, typ, lg), (normal, synth) in usage_counter.items():
        lookup_key = (typ, lg, cls, name)
        
        if lookup_key in row_lookup:
            # Update existing row
            row_idx = row_lookup[lookup_key]
            if synth:
                value = f"{normal}(+{synth})"
            else:
                value = str(normal)
            rows[row_idx][snapshot_label] = value
        else:
            # Create new row
            new_row = {col: '0' for col in fieldnames}
            new_row['Type'] = typ
            new_row['League'] = lg
            new_row['Class'] = cls
            new_row['Name'] = name
            if synth:
                value = f"{normal}(+{synth})"
            else:
                value = str(normal)
            new_row[snapshot_label] = value
            rows.append(new_row)
    
    # Save updated CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Updated {league} character data for {snapshot_label}")

def update_server_data_in_unified_csv(server_stats, game_servers, snapshot_label):
    """
    Update server metrics in unified CSV
    
    server_stats: dict with global server data
    game_servers: list of individual server data
    snapshot_label: string for the time period
    """
    csv_path = 'unified-usage-over-time.csv'
    
    # Load existing CSV
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Add new snapshot column if needed
    if snapshot_label not in fieldnames:
        fieldnames = list(fieldnames) + [snapshot_label]
        for row in rows:
            row[snapshot_label] = '0'
    
    # Create lookup
    row_lookup = {}
    for i, row in enumerate(rows):
        key = (row['Type'], row['League'], row['Class'], row['Name'])
        row_lookup[key] = i
    
    # Update global server stats
    server_mapping = {
        'online_now': 'Online_Now',
        'online_last_hour': 'Online_Last_Hour',
        'online_last_day': 'Online_Last_Day', 
        'online_last_week': 'Online_Last_Week',
        'online_last_fornight': 'Online_Last_Fortnight',
        'online_in_any_games': 'Online_In_Games',
        'games_open': 'Games_Open'
    }
    
    for api_key, csv_name in server_mapping.items():
        if api_key in server_stats:
            key = ('Server', 'ALL', '', csv_name)
            if key in row_lookup:
                # Clean the value (remove quotes)
                value = str(server_stats[api_key]).strip('"')
                rows[row_lookup[key]][snapshot_label] = value
            else:
                # Create new server metric row
                new_row = {col: '0' for col in fieldnames}
                new_row['Type'] = 'Server'
                new_row['League'] = 'ALL'
                new_row['Class'] = ''
                new_row['Name'] = csv_name
                value = str(server_stats[api_key]).strip('"')
                new_row[snapshot_label] = value
                rows.append(new_row)
    
    # Update individual game server stats
    for server in game_servers:
        country = server.get('country', 'Unknown').strip('"')
        location = server.get('location', 'Unknown')
        
        # Extract city name from location (before comma)
        city = location.split(',')[0].strip() if ',' in location else location
        city = city.replace(' ', '_')  # Replace spaces for CSV compatibility
        
        # Update players on this server
        players_key = ('GameServer', 'ALL', country, f'{city}_Players')
        if players_key in row_lookup:
            rows[row_lookup[players_key]][snapshot_label] = str(server.get('players', 0))
        else:
            # Create new game server row
            new_row = {col: '0' for col in fieldnames}
            new_row['Type'] = 'GameServer'
            new_row['League'] = 'ALL'
            new_row['Class'] = country
            new_row['Name'] = f'{city}_Players'
            new_row[snapshot_label] = str(server.get('players', 0))
            rows.append(new_row)
        
        # Update games on this server
        games_key = ('GameServer', 'ALL', country, f'{city}_Games')
        if games_key in row_lookup:
            rows[row_lookup[games_key]][snapshot_label] = str(server.get('games', 0))
        else:
            # Create new game server row
            new_row = {col: '0' for col in fieldnames}
            new_row['Type'] = 'GameServer'
            new_row['League'] = 'ALL'
            new_row['Class'] = country
            new_row['Name'] = f'{city}_Games'
            new_row[snapshot_label] = str(server.get('games', 0))
            rows.append(new_row)
    
    # Save updated CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Updated server data for {snapshot_label}")

def update_all_data(sc_characters=None, hc_characters=None, server_stats=None, game_servers=None, snapshot_label=None):
    """
    Convenience function to update all data types at once
    """
    if not snapshot_label:
        snapshot_label = datetime.now().strftime("%Y_%m_%d")
    
    if sc_characters:
        update_unified_csv_from_character_data(sc_characters, 'SC', snapshot_label)
    
    if hc_characters:
        update_unified_csv_from_character_data(hc_characters, 'HC', snapshot_label)
    
    if server_stats or game_servers:
        update_server_data_in_unified_csv(server_stats or {}, game_servers or [], snapshot_label)
    
    print(f"🎉 All data updated for {snapshot_label}")

# Example usage
if __name__ == "__main__":
    # Example: Load your existing character JSONs and update
    try:
        with open("sc_ladder.json") as f:
            sc_chars = json.load(f)
    except FileNotFoundError:
        sc_chars = None
        print("No sc_ladder.json found")
    
    try:
        with open("hc_ladder.json") as f:  # if you have this
            hc_chars = json.load(f)
    except FileNotFoundError:
        hc_chars = None
        print("No hc_ladder.json found")
    
    # Example server data (replace with your API calls)
    example_server_stats = {
        'online_now': 26,
        'online_last_hour': 37,
        'online_last_day': 142,
        'online_last_week': 357,
        'online_last_fornight': 488,
        'online_in_any_games': "28",
        'games_open': 31
    }
    
    example_game_servers = [
        {
            'gsID': 1,
            'max': 85,
            'country': '"US"',
            'location': '"Secaucus, NJ \\t&#9899;"',
            'games': 0,
            'players': 0
        }
    ]
    
    # Update everything
    update_all_data(
        sc_characters=sc_chars,
        hc_characters=hc_chars,
        server_stats=example_server_stats,
        game_servers=example_game_servers,
        snapshot_label="Test_Update"
    )