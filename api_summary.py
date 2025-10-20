#!/usr/bin/env python3
"""
Quick reference guide and utilities for the new unified CSV system
"""

import csv
from datetime import datetime

def show_data_summary():
    """Show a summary of what's in the unified CSV"""
    
    print("📊 UNIFIED CSV DATA SUMMARY")
    print("=" * 50)
    
    try:
        with open('unified-usage-over-time.csv', 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames
    except FileNotFoundError:
        print("❌ unified-usage-over-time.csv not found!")
        print("Run: python3 migrate_to_unified_csv.py")
        return
    
    # Count data types
    type_counts = {}
    league_counts = {}
    
    for row in rows:
        data_type = row['Type']
        league = row['League']
        
        type_counts[data_type] = type_counts.get(data_type, 0) + 1
        league_counts[league] = league_counts.get(league, 0) + 1
    
    print(f"📁 Total rows: {len(rows)}")
    print(f"📅 Time columns: {len(headers) - 4}")  # Minus Type, League, Class, Name
    print(f"🕐 Latest snapshot: {headers[-1]}")
    print()
    
    print("📋 DATA TYPES:")
    for data_type, count in sorted(type_counts.items()):
        print(f"   {data_type}: {count} rows")
    
    print("\n🏆 LEAGUES:")
    for league, count in sorted(league_counts.items()):
        print(f"   {league}: {count} rows")
    
    # Show recent server data
    print("\n🖥️ RECENT SERVER DATA:")
    latest_col = headers[-1]
    
    for row in rows:
        if row['Type'] == 'Server':
            name = row['Name']
            value = row[latest_col]
            print(f"   {name}: {value}")

def show_usage_examples():
    """Show usage examples for the new system"""
    
    print("\n🚀 USAGE EXAMPLES")
    print("=" * 50)
    
    print("💾 UPDATE DATA:")
    print("   python3 api_integration.py                    # Full update with 'Current [Month]'")
    print("   python3 api_integration.py 'S14 October'      # Season 14 October snapshot")
    print("   python3 api_integration.py 'November'         # November snapshot")
    print("   python3 api_integration.py 'End of Season'    # End of season snapshot")
    print("   python3 api_integration.py test               # Test API connections")
    print("   python3 api_integration.py suggest            # Show snapshot label suggestions")
    print()
    
    print("📊 MONITORING:")
    print("   python3 api_integration.py monitor            # Monitor every hour for 24 hours")
    print("   python3 api_integration.py monitor 30 48      # Every 30 min for 48 updates")
    print()
    
    print("🔍 ANALYSIS:")
    print("   python3 fun_facts_analysis.py                 # Run analysis (needs update)")
    print("   python3 api_integration.py web                # Generate web pages only")
    print("   python3 api_summary.py                        # This summary script")
    print()
    
    print("📁 FILES:")
    print("   unified-usage-over-time.csv                   # Main data file")
    print("   api_integration.py                            # Main update script")
    print("   sc-usage-over-time.html                       # SC web page")
    print("   hc-usage-over-time.html                       # HC web page") 
    print("   server-stats-over-time.html                   # Server analytics page")
    print("   migrate_to_unified_csv.py                     # One-time migration")
    print("   update_unified_csv.py                         # Helper functions")

def show_api_status():
    """Show current API status"""
    
    print("\n🌐 API STATUS CHECK")
    print("=" * 50)
    
    try:
        import requests
        
        # Test stats API
        try:
            response = requests.get('https://beta.pathofdiablo.com/api/stats', timeout=5)
            if response.status_code == 200:
                data = response.json()[0]
                print("✅ Stats API: Working")
                print(f"   Players online: {data.get('online_now', 'N/A')}")
                print(f"   Games open: {data.get('games_open', 'N/A')}")
            else:
                print(f"❌ Stats API: Error {response.status_code}")
        except Exception as e:
            print(f"❌ Stats API: {e}")
        
        # Test servers API
        try:
            response = requests.get('https://beta.pathofdiablo.com/api/servers', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Servers API: Working")
                print(f"   Active servers: {len(data)}")
                
                # Count active servers by region
                regions = {}
                for server in data:
                    country = server.get('country', 'Unknown').strip('"')
                    if server.get('players', 0) > 0:
                        regions[country] = regions.get(country, 0) + 1
                
                if regions:
                    print("   Active regions:", ', '.join(f"{k}({v})" for k, v in regions.items()))
            else:
                print(f"❌ Servers API: Error {response.status_code}")
        except Exception as e:
            print(f"❌ Servers API: {e}")
            
    except ImportError:
        print("❌ requests library not available")
        print("Install with: pip install requests")

def main():
    """Main function"""
    
    print("🎮 PATH OF DIABLO - UNIFIED ANALYTICS SYSTEM")
    print("=" * 60)
    
    show_data_summary()
    show_usage_examples()
    show_api_status()
    
    print("\n" + "=" * 60)
    print("🎉 System ready! Use the examples above to get started.")

if __name__ == "__main__":
    main()