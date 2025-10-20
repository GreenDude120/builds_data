#!/usr/bin/env python3
"""
Migration script to convert separate SC/HC CSVs into unified format
and add server data tracking capabilities.
"""

import csv
import json
from collections import defaultdict
from datetime import datetime

def migrate_to_unified_csv():
    """Convert existing SC/HC CSVs to unified format"""
    
    # Read both existing CSVs
    sc_data = []
    hc_data = []
    
    print("Reading existing SC CSV...")
    with open('sc-usage-over-time.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            row['League'] = 'SC'
            sc_data.append(row)
    
    print("Reading existing HC CSV...")
    with open('hc-usage-over-time.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['League'] = 'HC'
            hc_data.append(row)
    
    # Combine data
    all_data = sc_data + hc_data
    
    # New fieldnames with League column
    new_headers = ['Type', 'League', 'Class', 'Name'] + [h for h in headers if h not in ['Type', 'Class', 'Name']]
    
    # Write unified CSV
    print("Creating unified CSV...")
    with open('unified-usage-over-time.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_headers)
        writer.writeheader()
        writer.writerows(all_data)
    
    print("✅ Migration complete! Created 'unified-usage-over-time.csv'")
    print(f"📊 Migrated {len(sc_data)} SC rows and {len(hc_data)} HC rows")
    
    return new_headers

def add_sample_server_data(headers):
    """Add sample server data to demonstrate the structure"""
    
    # Sample server metrics (you'll replace this with your real API data)
    sample_server_data = [
        # Global server stats
        {'Type': 'Server', 'League': 'ALL', 'Class': '', 'Name': 'Online_Now'},
        {'Type': 'Server', 'League': 'ALL', 'Class': '', 'Name': 'Online_Last_Hour'},
        {'Type': 'Server', 'League': 'ALL', 'Class': '', 'Name': 'Online_Last_Day'},
        {'Type': 'Server', 'League': 'ALL', 'Class': '', 'Name': 'Online_Last_Week'},
        {'Type': 'Server', 'League': 'ALL', 'Class': '', 'Name': 'Online_Last_Fortnight'},
        {'Type': 'Server', 'League': 'ALL', 'Class': '', 'Name': 'Games_Open'},
        
        # Individual game server stats
        {'Type': 'GameServer', 'League': 'ALL', 'Class': 'US', 'Name': 'Secaucus_Players'},
        {'Type': 'GameServer', 'League': 'ALL', 'Class': 'US', 'Name': 'Secaucus_Games'},
        {'Type': 'GameServer', 'League': 'ALL', 'Class': 'EU', 'Name': 'Frankfurt_Players'},
        {'Type': 'GameServer', 'League': 'ALL', 'Class': 'EU', 'Name': 'Frankfurt_Games'},
    ]
    
    # Initialize all time columns with 0
    for row in sample_server_data:
        for header in headers:
            if header not in ['Type', 'League', 'Class', 'Name']:
                row[header] = '0'
    
    # Read existing unified CSV
    existing_data = []
    with open('unified-usage-over-time.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        existing_data = list(reader)
    
    # Append server data
    all_data = existing_data + sample_server_data
    
    # Write back
    with open('unified-usage-over-time.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_data)
    
    print("✅ Added sample server data structure")
    print("📝 You can now update server metrics using update_server_data()")

def update_server_data(server_stats, game_servers, snapshot_label):
    """
    Update server data in unified CSV
    
    server_stats: dict with keys like 'online_now', 'online_last_hour', etc.
    game_servers: list of dicts with 'gsID', 'players', 'games', 'country', etc.
    snapshot_label: string like 'November' or 'Week_1'
    """
    
    # Read existing CSV
    with open('unified-usage-over-time.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Add new snapshot column if it doesn't exist
    if snapshot_label not in fieldnames:
        fieldnames = list(fieldnames) + [snapshot_label]
        for row in rows:
            row[snapshot_label] = '0'
    
    # Create lookup for easy updates
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
        'games_open': 'Games_Open'
    }
    
    for api_key, csv_name in server_mapping.items():
        if api_key in server_stats:
            key = ('Server', 'ALL', '', csv_name)
            if key in row_lookup:
                rows[row_lookup[key]][snapshot_label] = str(server_stats[api_key])
    
    # Update individual game server stats
    for server in game_servers:
        country = server.get('country', 'Unknown').strip('"')
        location_parts = server.get('location', '').split()
        city = location_parts[0] if location_parts else 'Unknown'
        
        # Players on this server
        players_key = ('GameServer', 'ALL', country, f'{city}_Players')
        if players_key in row_lookup:
            rows[row_lookup[players_key]][snapshot_label] = str(server.get('players', 0))
        
        # Games on this server  
        games_key = ('GameServer', 'ALL', country, f'{city}_Games')
        if games_key in row_lookup:
            rows[row_lookup[games_key]][snapshot_label] = str(server.get('games', 0))
    
    # Write updated CSV
    with open('unified-usage-over-time.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Updated server data for {snapshot_label}")

# Example usage
if __name__ == "__main__":
    # Step 1: Migrate existing data
    headers = migrate_to_unified_csv()
    
    # Step 2: Add server data structure
    add_sample_server_data(headers)
    
    # Step 3: Example of updating server data (you'd call this with real API data)
    sample_server_stats = {
        'online_now': 26,
        'online_last_hour': 37,
        'online_last_day': 142,
        'online_last_week': 357,
        'online_last_fornight': 488,
        'games_open': 31
    }
    
    sample_game_servers = [
        {
            'gsID': 1,
            'max': 85,
            'country': 'US',
            'location': 'Secaucus, NJ',
            'games': 12,
            'players': 45
        },
        {
            'gsID': 2, 
            'max': 75,
            'country': 'EU',
            'location': 'Frankfurt, DE',
            'games': 8,
            'players': 23
        }
    ]
    
    update_server_data(sample_server_stats, sample_game_servers, 'Current_Test')
    
    print("\n🎉 Migration complete!")
    print("📁 Your unified CSV is ready with server data tracking")
    print("🔄 Update your analysis script to use 'unified-usage-over-time.csv'")