#
#   V3
#   This will be the first to try using one single json file instead of folders full of jsons
#
###############################################################
# Functions included here:
# GetAllCharData - pulls down ladder top 1,000, does not care about class
# GetClassCharData - Pulls down the top 200 of each class, verifies class is correct
#       If a ladder character or parent account is deleted, the name remains on the ladder, this can cause the 
#       same name to be reused allowing the same character file to exist in more than one class folder, this checks for that
# MakeHome - This creates the home page; uses data from GetAllCharData
# GetNonZon - Gets non-zon characters that have bolts or arrows equipped, creates charts and html. Uses data from GetClassCharData
# GetUniqueProjectiles - Looks for unique arrows and bolts equipped, uses data from GetClassCharData
# GetBong() - Gets Bong and Warpspear, uses data from GetClassCharData
# GetDashers - Dashing Strike builds, uses data from GetClassCharData
# GetChargers - Gets characters with 10+ points in charge or wearing templars, uses data from GetClassCharData
# GetOffensiveAuraItemsEquipped - Get character with 2 or more aura granting items
# MakeClassPages - Makes the html pages for each class, uses data from GetClassCharData
#       Skill weights live here
# GitHubSync - Pushes all changes to Github; This should always be called last
###############################################################


# Used to create data read by manual-forced-cluster2.py
import requests
import os
import time
# Get non zon
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import plotly.express as px
import json
import os
from jinja2 import Template
from collections import Counter, defaultdict
import pprint
pp = pprint.PrettyPrinter(indent=4)
from datetime import datetime
import subprocess
from datetime import datetime
import items_list
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


###############################################################
#
# Pull down character data
#
# Base URLs

import os
import json
import time
import requests

def DownloadLadderData(mode="both"):  # "sc", "hc", or "both"
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/"
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"

    # Define ladder ranking APIs (we now loop dynamically instead of using a fixed list)
    classes = [
        {"what_class": "Amazon", "api": "1"},
        {"what_class": "Sorceress", "api": "2"},
        {"what_class": "Necromancer", "api": "3"},
        {"what_class": "Paladin", "api": "4"},
        {"what_class": "Barbarian", "api": "5"},
        {"what_class": "Druid", "api": "6"},
        {"what_class": "Assassin", "api": "7"},
    ]

    # Select which modes to process
    modes = []
    if mode in ["sc", "both"]:
        modes.append(("sc", base_ladder_url + "0/"))
    if mode in ["hc", "both"]:
        modes.append(("hc", base_ladder_url + "1/"))

    # Process each mode
    for sc_or_hc, ladder_url in modes:
        all_characters = {}  # Dictionary to store character data (no duplicates)

        # Fetch Top 1,000+ characters (keep requesting pages until we stop getting results)
        ProcessLadderPagesDynamically(ladder_url, char_url, all_characters)

        # Fetch Top 200 per class
        for cls in classes:
            ProcessLadderPagesDynamically(ladder_url, char_url, all_characters, cls["api"])

        # Save everything in a single JSON file
        save_path = f"jsons/{sc_or_hc}.json"
        with open(save_path, "w") as file:
            json.dump(all_characters, file, indent=4)

        print(f"✅ {sc_or_hc.upper()} ladder data saved to {save_path} (Total: {len(all_characters)} characters)")

def ProcessLadderPagesDynamically(base_url, char_url, all_characters, class_api="0"):
    """Fetches ladder data dynamically, continuing until no more results are found."""
    page = 1  # Start at page 1

    while True:
        url = f"{base_url}{class_api}/{page}"
        response = requests.get(url)
        
        try:
            ladder_data = response.json()
            characters = ladder_data.get("ladder", [])

            if not characters:
                print(f"✅ Finished fetching {url} (No more characters found)")
                break  # Stop if we get an empty list

            for character in characters:
                char_name = character.get("charName", "unknown")
                char_id = character.get("id", None)

                if char_name == "unknown":
                    char_name = f"unknown_{char_id or int(time.time() * 1000)}"

                # Avoid fetching duplicate characters
                if char_name in all_characters:
                    continue

                char_response = requests.get(char_url.format(char_name=char_name))
                all_characters[char_name] = char_response.json()  # Store in dictionary

                print(f"✅ Added {char_name} from {url}")

            page += 1  # Move to the next page

        except Exception as e:
            print(f"⚠️ Error processing {url}: {e}")
            break  # Stop on error


############################
#
# Use these  
# 
def fetch_ladder_characters(base_ladder_url, pages):
    """Fetch all characters from multiple pages of the ladder."""
    all_characters = []
    for page in range(0, pages + 1):
        ladder_url = f"{base_ladder_url}{page}"
        print(f"Fetching {ladder_url}")
        response = requests.get(ladder_url)
        if response.status_code == 200:
            ladder_data = response.json()
            all_characters.extend(ladder_data.get("ladder", []))
        else:
            print(f"⚠️ Failed to fetch page {page}: {response.status_code}")
    return all_characters

def count_classes(characters):
    """Count the class distribution for the top 1,000 characters."""
    return Counter(char.get("charClass", "Unknown") for char in characters)

def generate_pie_chart(class_counts):
    """Generate a pie chart for class distribution of the top 1,000 characters."""
    classes = list(class_counts.keys())
    counts = list(class_counts.values())

    if not counts:
        print("⚠️ No characters found for pie chart.")
        return

    armory = FontProperties(fname='armory/font/avqest.ttf')  # Update path if needed

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f'{pct:.1f}% ({val})'
        return my_autopct

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figure(figsize=(22, 22))
    plt.subplots_adjust(top=0.5, bottom=0.15)

    wedges, texts, autotexts = plt.pie(
        counts, labels=classes, autopct=make_autopct(counts), startangle=250,
        colors=plt.cm.Paired.colors, radius=1.4,
        textprops={'fontsize': 30, 'color': 'white', 'fontproperties': armory}
    )

    title = plt.title(
        f"Class Distribution of Top 1,000 Characters\n\nAs of {timestamp}",
        pad=50, fontsize=45, fontproperties=armory, loc='left', color="white"
    )
    title.set_fontsize(45)  # 🔹 Force title size after creation

    for text in texts:
        text.set_fontsize(35)  # Class labels
    for autotext in autotexts:
        autotext.set_fontsize(25)  # Percentages on slices
        autotext.set_color('black')

    plt.axis('equal')  # Ensures the pie chart is circular
    plt.savefig("pod-stats/charts/1kclass_distribution.png", dpi=300, bbox_inches='tight', transparent=True)
    plt.close()  # Avoid memory issues
    print("✅ Pie chart saved as class_distribution.png")

def generate_pie_chart_all(class_counts):
    """Generate a pie chart for class distribution of the top 1,000 characters."""
    classes = list(class_counts.keys())
    counts = list(class_counts.values())

    if not counts:
        print("⚠️ No characters found for pie chart.")
        return

    armory = FontProperties(fname='armory/font/avqest.ttf')  # Update path if needed

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f'{pct:.1f}% ({val})'
        return my_autopct

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figure(figsize=(22, 22))
    plt.subplots_adjust(top=0.5, bottom=0.15)

    wedges, texts, autotexts = plt.pie(
        counts, labels=classes, autopct=make_autopct(counts), startangle=250,
        colors=plt.cm.Paired.colors, radius=1.4,
        textprops={'fontsize': 30, 'color': 'white', 'fontproperties': armory}
    )

    title = plt.title(
        f"Class Distribution of Top 1,000 Characters\n\nAs of {timestamp}",
        pad=50, fontsize=45, fontproperties=armory, loc='left', color="white"
    )

    # Adjust font sizes for labels and percentages
    for text in texts:
        text.set_fontsize(35)
    for autotext in autotexts:
        autotext.set_fontsize(25)
        autotext.set_color('black')

    plt.axis('equal')  # Ensures the pie chart is circular
    plt.savefig("pod-stats/charts/all_class_distribution.png", dpi=300, bbox_inches='tight', transparent=True)
    plt.close()  # Avoid memory issues
    print("✅ Pie chart saved as all_class_distribution.png")

def GetAllCharData():
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/0/"  # Softcore
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"

    # Step 1: Fetch top 1,000 characters (pages 0 to 5)
    all_characters = fetch_ladder_characters(f"{base_ladder_url}0/", 5)
    top_1000_characters = {char["charName"]: char for char in all_characters}.values()

    # Step 2: Create pie chart from the top 1,000 characters
    class_counts = count_classes(top_1000_characters)
    generate_pie_chart(class_counts)

    # Step 3: Continue with class-specific characters
    classes = {
        "Amazon": "1/",
        "Assassin": "7/",
        "Barbarian": "5/",
        "Druid": "6/",
        "Necromancer": "3/",
        "Paladin": "4/",
        "Sorceress": "2/"
    }

    for class_name, api_suffix in classes.items():
        class_ladder_url = f"{base_ladder_url}{api_suffix}"
        class_characters = fetch_ladder_characters(class_ladder_url, 1)
        all_characters.extend(class_characters)  # Combine lists

    # Step 4: Remove duplicates by character name
    unique_characters = {char["charName"]: char for char in all_characters}.values()

#    class_counts = count_classes(unique_characters) # if we wanted a pie chart generated here, i think it's fine to keep in makehome
#    generate_pie_chart_all(class_counts)

    # Step 5: Fetch complete character data
    character_data = []
    for character in unique_characters:
        char_name = character.get("charName", "unknown")
        char_id = character.get("id", None)

        if char_name == "unknown":
            char_name = f"unknown_{char_id or int(time.time() * 1000)}"

        response = requests.get(char_url.format(char_name=char_name))
        if response.status_code == 200:
            character_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character: {char_name}")

    # Step 6: Save the extended character list
    with open("sc_ladder.json", "w") as file:
        json.dump(character_data, file, indent=2)

    print(f"✅ Saved {len(character_data)} characters to sc_ladder.json (top 1,000 + class-specific)")


# Run commands
#GetAllCharData()
#DownloadLadderData("sc")
#DownloadLadderData("hc")
#DownloadLadderData("both")

###############################################################
#
# Create home page
#
def MakeHome():
    # Define the consolidated JSON file path
    consolidated_file = "sc_ladder.json"  # Replace with your actual file path
    
    try:
        # Load the consolidated JSON file
        with open(consolidated_file, "r") as file:
            all_characters = json.load(file)
            all_characters = [json.loads(char) if isinstance(char, str) else char for char in all_characters]

        
        # Add this print statement to inspect the structure of the data
        print("First 5 entries in all_characters:", all_characters[:5])  # Debugging output
        print("Type of all_characters:", type(all_characters))  # Check if it's a list
        if isinstance(all_characters[0], str):  # Check if elements are strings
            print("First entry as string:", all_characters[0])  # Print one raw string entry
        
        # Convert strings to dictionaries if needed
        if isinstance(all_characters[0], str):  # If first element is a string
            all_characters = [json.loads(char_data) for char_data in all_characters]
            print("Converted all_characters to dictionaries.")  # Confirmation message
        
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading consolidated JSON file: {e}")
        return

    # Now you can safely process the characters
    try:
        class_counts, runeword_counter, unique_counter, set_counter, synth_counter = process_all_characters(all_characters)
        # Continue with the rest of your MakeHome logic...
    except Exception as e:
        print(f"Error during character processing: {e}")

#    data_folder = "sc/ladder-all"
    html_output = """"""
    output_file = "all_mercenary_report.html"
    synth_item = "Synth"


    dt = datetime.now()
    # format it to a string
    timeStamp = dt.strftime('%Y-%m-%d %H:%M')

    # Counters for classes, runewords, uniques, and set items
    class_counts = {}
    runeword_counter = Counter()
    unique_counter = Counter()
    set_counter = Counter()
    synth_counter = Counter()
    crafted_counters = {
        "Rings": Counter(),
        "Weapons and Shields": Counter(),
        "Arrows": Counter(),
        "Bolts": Counter(),
        "Body Armor": Counter(),
        "Gloves": Counter(),
        "Belts": Counter(),
        "Helmets": Counter(),
        "Boots": Counter(),
        "Amulets": Counter(),
    }
    magic_counters = {
        "Rings": Counter(),
        "Weapons and Shields": Counter(),
        "Arrows": Counter(),
        "Bolts": Counter(),
        "Body Armor": Counter(),
        "Gloves": Counter(),
        "Belts": Counter(),
        "Helmets": Counter(),
        "Boots": Counter(),
        "Amulets": Counter(),
    }
    rare_counters = {
        "Rings": Counter(),
        "Weapons and Shields": Counter(),
        "Arrows": Counter(),
        "Bolts": Counter(),
        "Body Armor": Counter(),
        "Gloves": Counter(),
        "Belts": Counter(),
        "Helmets": Counter(),
        "Boots": Counter(),
        "Amulets": Counter(),
    }
    
    synth_sources = {}  # Maps item names to all synth items that used them

    runeword_users = {}
    unique_users = {}
    set_users = {}
    synth_users = {}
    crafted_users = {category: {} for category in crafted_counters}  # Ensure all categories exist
    rare_users = {category: {} for category in rare_counters}  # Ensure all categories exist
    magic_users = {category: {} for category in magic_counters}  # Ensure all categories exist

    all_characters = []
    sorted_just_socketed_runes = {}
    sorted_just_socketed_excluding_runewords_runes = {}
    all_other_items = {}


    
    # Function to process each JSON file
    def process_all_characters():
        with open("sc_ladder.json", "r") as file:
            all_characters = json.load(file)  # Ensure it's a list of dictionaries

        for char_data in all_characters:
            if isinstance(char_data, str):  # If somehow it's still a string, convert it
                char_data = json.loads(char_data)

            char_name = char_data.get("Name", "Unknown")  # This should now work
            print(f"Processing {char_name}")
            char_class = char_data.get("Class", "Unknown")
            char_level = char_data.get("Stats", {}).get("Level", "Unknown")

            # Debugging: Print details of the character being processed
            print(f"Processing character: {char_name}, Class: {char_class}, Level: {char_level}")

            # Continue with processing logic (e.g., class counts, equipped items, etc.)

        # Dictionary to store class counts
        class_counts = {}

        # Counters for runewords, uniques, and set items
        runeword_counter = Counter()
        unique_counter = Counter()
        set_counter = Counter()
        synth_counter = Counter()

        # Categorize worn slots
        def categorize_worn_slot(worn_category, text_tag):
            if worn_category in ["sweapon1", "weapon1", "sweapon2", "weapon2"]:
                if text_tag == "Arrows":
                    return "Arrows"
                elif text_tag == "Bolts":
                    return "Bolts"
                else:
                    return "Weapons and Shields"

            worn_category_map = {
                "ring1": "Rings", "ring2": "Rings",
                "body": "Armor",
                "gloves": "Gloves",
                "belt": "Belts",
                "helmet": "Helmets",
                "boots": "Boots",
                "amulet": "Amulets",
            }

            return worn_category_map.get(worn_category, "Other")  # Default to "Other"

        # Process each character in the consolidated JSON
        for char_data in all_characters:
            try:
                char_name = char_data.get("Name", "Unknown")
                char_class = char_data.get("Class", "Unknown")
                char_level = char_data.get("Stats", {}).get("Level", "Unknown")

                # Process class data
                if char_class:
                    class_counts[char_class] = class_counts.get(char_class, 0) + 1

                # Process equipped items
                for item in char_data.get("Equipped", []):
                    worn_category = categorize_worn_slot(item.get("Worn", ""), item.get("TextTag", ""))  # ✅ Call once

                    character_info = {
                        "name": char_name,
                        "class": char_class,
                        "level": char_level,
                    }

                    if "synth" in item.get("Tag", "").lower() or "synth" in item.get("TextTag", "").lower():
                        item_title = item["Title"]
                        synth_counter[item_title] += 1
                        synth_users.setdefault(item_title, []).append(character_info)

                        # Process SynthesisedFrom property
                        synthesized_from = item.get("SynthesisedFrom", [])
                        all_related_items = [item_title] + synthesized_from
                        for source_item in all_related_items:
                            synth_sources.setdefault(source_item, []).append({
                                "name": char_name,
                                "class": char_class,
                                "level": char_level,
                                "synthesized_item": item_title
                            })

                    if item.get("QualityCode") == "q_runeword":
                        title = item["Title"]
                        
                        # ✅ Change "2693" to "Delirium"
                        if title == "2693":
                            title = "Delirium"
                        if title == "-26":
                            title == "Pattern2"
                        
                        runeword_counter[title] += 1
                        runeword_users.setdefault(title, []).append(character_info)

                    if item.get("QualityCode") == "q_unique":
                        unique_counter[item["Title"]] += 1
                        unique_users.setdefault(item["Title"], []).append(character_info)

                    if item.get("QualityCode") == "q_set":
                        set_counter[item["Title"]] += 1
                        set_users.setdefault(item["Title"], []).append(character_info)

                    if item.get("QualityCode") == "q_crafted":
                        crafted_counters[worn_category][item["Title"]] += 1
                        crafted_users.setdefault(worn_category, {}).setdefault(item["Title"], []).append(character_info)

            except (KeyError, TypeError) as e:
                print(f"Error processing character: {char_name}, Error: {e}")
                continue

#        return class_counts, runeword_counter, unique_counter, set_counter, synth_counter
        return class_counts, runeword_counter, unique_counter, set_counter, synth_counter, runeword_users, unique_users, set_users, synth_users, crafted_counters, crafted_users

    def process_magic_and_rare_items(all_characters, magic_counters, rare_counters, magic_users, rare_users):
        with open("sc_ladder.json", "r") as file:
            all_characters = json.load(file)  # Ensure it's a list of dictionaries
        print(f"Total characters loaded by process_magic_and_rare_items: {len(all_characters)}")
#        equipped_items = char_data.get("Equipped", [])
#        print(f"Equipped: {equipped_items}")  # Prints raw data
        magic_counters = {category: Counter() for category in magic_counters}
        rare_counters = {category: Counter() for category in rare_counters}
        magic_users = {category: {} for category in magic_counters}
        rare_users = {category: {} for category in rare_counters}

        def categorize_worn_slot(worn_category, text_tag):
            if worn_category in ["sweapon1", "weapon1", "sweapon2", "weapon2"]:
                if text_tag == "Arrows":
                    return "Arrows"
                elif text_tag == "Bolts":
                    return "Bolts"
                else:
                    return "Weapons and Shields"

            worn_category_map = {
                "ring1": "Rings", "ring2": "Rings",
                "body": "Armor",
                "gloves": "Gloves",
                "belt": "Belts",
                "helmet": "Helmets",
                "boots": "Boots",
                "amulet": "Amulets",
            }

            return worn_category_map.get(worn_category, "Other")  # Default to "Other"

        # Process each character in the consolidated JSON
        for char_data in all_characters:
#            print(f"Checking {char_data.get('Name', 'Unknown')} - Equipped items: {len(char_data.get('Equipped', []))}")
            try:
                char_name = char_data.get("Name", "Unknown")
                char_class = char_data.get("Class", "Unknown")
                char_level = char_data.get("Stats", {}).get("Level", "Unknown")
                character_info = {"name": char_name, "class": char_class, "level": char_level}

                seen_magic_items = {category: set() for category in magic_counters}
                seen_rare_items = {category: set() for category in rare_counters}

                for item in char_data.get("Equipped", []):
                    worn_category = categorize_worn_slot(item.get("Worn", ""), item.get("TextTag", ""))
                    character_info = {"name": char_name, "class": char_class, "level": char_level}

                    if item.get("QualityCode") == "q_magic":
                        magic_counters[worn_category][item["Title"]] += 1
                        magic_users.setdefault(worn_category, {}).setdefault(item["Title"], []).append(character_info)

                    if item.get("QualityCode") == "q_rare":
                        rare_counters[worn_category][item["Title"]] += 1
                        rare_users.setdefault(worn_category, {}).setdefault(item["Title"], []).append(character_info)

            except (KeyError, TypeError) as e:
                print(f"Error processing character: {char_name}, Error: {e}")
                continue

        return magic_counters, magic_users, rare_counters, rare_users

    def GetSCFunFacts():
        # Path to the consolidated JSON file
        consolidated_file = "sc_ladder.json"

        # Load character data from the consolidated JSON file
        try:
            with open(consolidated_file, "r") as file:
                characters = json.load(file)  # Load all characters into a list
            print(all_characters[:5])  # Display the first 5 elements

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading consolidated JSON file: {e}")
            return ""

        # Extract alive characters
        alive_characters = [char for char in characters if not char.get("IsDead", True)]
        undead_count = len(alive_characters)

        # Function to format the alive characters list
        def GetTheLiving():
            return "".join(
                f"""
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char.get("Name", "Unknown")}" target="_blank">
                            {char.get("Name", "Unknown")}
                        </a>
                    </div>
                    <div>Level {char.get("Stats", {}).get("Level", "N/A")} {char.get("Class", "Unknown")}</div>
                    <div class="hover-trigger" data-character-name="{char.get("Name", "Unknown")}"></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div> <!-- No iframe inside initially -->
                </div>
                """
                for char in alive_characters
            )

        alive_list_html = GetTheLiving()

        # Function to get top 5 characters for a given stat
        def get_top_characters(stat_name):
            ranked = sorted(
                characters,
                key=lambda c: c.get("Stats", {}).get(stat_name, 0) + c.get("Bonus", {}).get(stat_name, 0),
                reverse=True,
            )[:5]

            return "".join(
                f"""<li>&nbsp;&nbsp;&nbsp;&nbsp;
                    <a href="https://pathofdiablo.com/p/armory/?name={char.get('Name', 'Unknown')}" target="_blank">
                        {char.get('Name', 'Unknown')} ({char.get('Stats', {}).get(stat_name, 0) + char.get('Bonus', {}).get(stat_name, 0)})
                    </a>
                </li>"""
                for char in ranked
            )

        # Get the top 5 for each stat
        top_strength = get_top_characters("Strength")
        top_dexterity = get_top_characters("Dexterity")
        top_vitality = get_top_characters("Vitality")
        top_energy = get_top_characters("Energy")
        top_life = get_top_characters("Life")
        top_mana = get_top_characters("Mana")

        # Compute Magic Find (MF) and Gold Find (GF)
        total_mf = 0
        total_gf = 0
        total_life = 0
        total_mana = 0
        character_count = len(characters)

        for char in characters:
            mf = char.get("Bonus", {}).get("MagicFind", 0)
            gf = char.get("Bonus", {}).get("GoldFind", 0)
            mf += char.get("Bonus", {}).get("WeaponSetMain", {}).get("MagicFind", 0)
            mf += char.get("Bonus", {}).get("WeaponSetOffhand", {}).get("MagicFind", 0)
            gf += char.get("Bonus", {}).get("WeaponSetMain", {}).get("GoldFind", 0)
            gf += char.get("Bonus", {}).get("WeaponSetOffhand", {}).get("GoldFind", 0)
            life = char.get("Stats", {}).get("Life", 0)
            mana = char.get("Stats", {}).get("Mana", 0)
            total_mf += mf
            total_gf += gf
            total_life += life
            total_mana += mana

        top_magic_find = get_top_characters("MagicFind")
        top_gold_find = get_top_characters("GoldFind")

        # Calculate averages
        average_mf = total_mf / character_count if character_count > 0 else 0
        average_gf = total_gf / character_count if character_count > 0 else 0
        average_life = total_life / character_count if character_count > 0 else 0
        average_mana = total_mana / character_count if character_count > 0 else 0

        # Generate fun facts HTML
        fun_facts_html = f"""
        <h3>Softcore Fun Facts</h3>
            <h3>{undead_count} Characters in the Softcore top {character_count} have not died</h3>
                <button type="button" class="collapsible sets-button">
                    <img src="icons/Special_click.png" alt="Undead Open" class="icon open-icon hidden">
                    <img src="icons/Special.png" alt="Undead Close" class="icon close-icon">
                </button>
                <div class="content">  
                    <div id="special">{alive_list_html}</div>
                </div>
        <br>

        <!-- Strength & Dexterity Row -->
        <div class="fun-facts-row">
            <div class="fun-facts-column">
                <h3>Top 5 Characters with the most Strength:</h3>
                <ul>{top_strength}</ul>
            </div>
            <div class="fun-facts-column">
                <h3>Top 5 Characters with the most Dexterity:</h3>
                <ul>{top_dexterity}</ul>
            </div>
        </div>

        <!-- Vitality & Energy Row -->
        <div class="fun-facts-row">
            <div class="fun-facts-column">
                <h3>Top 5 Characters with the most Vitality:</h3>
                <ul>{top_vitality}</ul>
            </div>
            <div class="fun-facts-column">
                <h3>Top 5 Characters with the most Energy:</h3>
                <ul>{top_energy}</ul>
            </div>
        </div>

        <!-- Life & Mana Row -->
        <div class="fun-facts-row">
            <div class="fun-facts-column">
                <h3>The 5 Characters with the Most Life*:</h3>
                <ul>{top_life}</ul>
                <p><strong>Average Life:</strong> {average_life:.2f}</p>
            </div>
            <div class="fun-facts-column">
                <h3>The 5 Characters with the Most Mana*:</h3>
                <ul>{top_mana}</ul>
                <p><strong>Average Mana:</strong> {average_mana:.2f}</p>
            </div>
        </div>
        <em>*"Most" Life and Mana values are from a snapshot in time and may or may not be affected by bonuses from BO, Oak, etc.</em>
        <!-- Magic Find & Gold Find Row -->
        <div class="fun-facts-row">
            <div class="fun-facts-column">
                <h3>The 5 Characters with the Most Magic Find:</h3>
                <ul>{top_magic_find}</ul>
                <p><strong>Average Magic Find:</strong> {average_mf:.2f}</p>
            </div>
            <div class="fun-facts-column">
                <h3>The 5 Characters with the Most Gold Find:</h3>
                <ul>{top_gold_find}</ul>
                <p><strong>Average Gold Find:</strong> {average_gf:.2f}</p>
            </div>
        </div>
        """

        return fun_facts_html

    # Generate fun facts
    fun_facts_html = GetSCFunFacts()

    # Process the files in the data folder
    class_counts, runeword_counter, unique_counter, set_counter, synth_counter, runeword_users, unique_users, set_users, synth_users, crafted_counters, crafted_users = process_all_characters()
    magic_counters, magic_users, rare_counters, rare_users = process_magic_and_rare_items(all_characters, magic_counters, rare_counters, magic_users, rare_users)

    # Print the class counts
    print("Class Counts:")
    for char_class, count in class_counts.items():
        print(f"{char_class}: {count} characters")

    # Print the most and least common items
    def print_item_counts(title, counter):
        print(f"\n{title}:")
        most_common = counter.most_common(10)
        least_common = counter.most_common()[:-11:-1]
        for item, count in most_common:
            print(f"Most common - {item}: {count}")
        for item, count in least_common:
            print(f"Least common - {item}: {count}")

    #print_item_counts("Runewords", runeword_counter)
    #print_item_counts("Uniques", unique_counter)
    #print_item_counts("Set Items", set_counter)

    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.font_manager import FontProperties

    # Generate pie chart data
    classes = list(class_counts.keys())
    counts = list(class_counts.values())
    total = sum(counts)


    # Load custom font
     # Load custom font
    armory = FontProperties(fname='armory/font/avqest.ttf')  # Update path if needed

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f'{pct:.1f}% ({val})'
        return my_autopct

    # Timestamp for title
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Set figure size
    plt.figure(figsize=(22, 22))
    plt.subplots_adjust(top=0.5, bottom=0.15)

    # Create the pie chart
    wedges, texts, autotexts = plt.pie(
        counts, labels=classes, autopct=make_autopct(counts), startangle=250, 
        colors=plt.cm.Paired.colors, radius=1.4, textprops={'fontsize': 30, 'color': 'white', 'fontproperties': armory}
    )


    title = plt.title(
        f"Class Distribution, ALL characters with a ladder ranking\n\nAs of {timestamp}", 
        pad=50, fontsize=40, fontproperties=armory, loc='left', color="white"
    )
    title.set_fontsize(45)  # 🔹 Force title size after creation

    for text in texts:
        text.set_fontsize(35)  # Class labels
    for autotext in autotexts:
        autotext.set_fontsize(25)  # Percentages on slices
        autotext.set_color('black')

    plt.axis('equal')  # Ensures the pie chart is circular

    # Save the plot with transparent background
    plt.savefig("pod-stats/charts/class_distribution.png", dpi=300, bbox_inches='tight', transparent=True)

    print("Plot saved as class_distribution.png")

    # Display the plot
    plt.show()


    # Get the most common items
    most_common_runewords = runeword_counter.most_common(10)
    most_common_uniques = unique_counter.most_common(10)
    most_common_set_items = set_counter.most_common(10)

    # Get all the items
    all_uniques = unique_counter.most_common(150)
    all_runewords = runeword_counter.most_common(150)
    all_uniques_all = unique_counter.most_common(400)
    all_set = set_counter.most_common(150)
    all_synth = synth_counter.most_common(150)

    # Get the least common items
    least_common_runewords = runeword_counter.most_common()[:-11:-1]
    least_common_uniques = unique_counter.most_common()[:-11:-1]
    least_common_set_items = set_counter.most_common()[:-11:-1]


    # Generate list items
    def generate_list_items(items):
        return ''.join(
            f'<li>{"Delirium" if item == "2693" else "Pattern2" if item == "-26" else item}: {count}</li>'
#            f'<li>{"Pattern" if item == "-26" else item}: {count}</li>'
            for item, count in items
        )

    def generate_all_list_items(counter, character_data):
        if not isinstance(character_data, list):
            print("Error: character_data is not a list! Type:", type(character_data))
            return ""  # Return an empty string to avoid breaking HTML generation

        items_html = ""

        for item, count in counter:
            display_item = "Delirium" if item == "2693" else "Pattern2" if item == "-26" else item # ✅ Replace "2693" with "Delirium"

            # Handle normal cases
            if counter != synth_counter:
                character_list = [
                    char
                    for char in character_data
                    if isinstance(char, dict) and any(
                        (equipped_item.get("Title") == item or (equipped_item.get("Title") == "2693" and item == "Delirium") or (equipped_item.get("Title") == "-26" and item == "Pattern2"))
                        for equipped_item in char.get("Equipped", [])
                    )
                ]
            # Handle synth items separately
            if counter == synth_counter:
                character_list = [
                    char for char in synth_users.get(item, [])
                    if "synth" in char["item"].get("Tag", "").lower() or "synth" in char["item"].get("TextTag", "").lower()
                ]

            character_list_html = "".join(
                f""" 
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["Name"]}" target="_blank">
                            {char["Name"]}
                        </a>
                    </div>
                    <div>Level {char["Stats"]["Level"]} {char["Class"]}</div>
                    <div class="hover-trigger" data-character-name="{char["Name"]}"><!-- Armory Quickview--></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div> <!-- No iframe inside initially -->
                </div>
                """
                for char in character_list
            )

            items_html += f"""
            <button class="collapsible">
                <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                <strong>{display_item} ({count} users)</strong>
            </button>
            <div class="content">
                {character_list_html if character_list else "<p>No characters using this item.</p>"}
            </div>
            """

        return items_html

    def generate_synth_list_items(counter: Counter, synth_users: dict):
        items_html = ""
#        for item, count in counter.items():
        for item, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):

            character_list = synth_users.get(item, [])  # Directly fetch correct list

            character_list_html = "".join(
                f""" 
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}
                        </a>
                    </div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div> <!-- No iframe inside initially -->
                </div>
                """ for char in character_list
            )

            items_html += f""" 
            <button class="collapsible">
                <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                <strong>{item} ({count} users)</strong>
            </button>
            <div class="content">
                {character_list_html if character_list else "<p>No characters using this item.</p>"}
            </div>
            """
        
        return items_html

    synth_user_count = sum(len(users) for users in synth_users.values())

    def generate_synth_source_list(synth_sources):
        items_html = ""

#        for source_item, characters in synth_sources.items():
        for source_item, characters in sorted(synth_sources.items(), key=lambda x: (-len(x[1]), x[0])):
    
            character_list_html = "".join(
                f"""
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}
                        </a>
                    </div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div>Used in: <strong>{char["synthesized_item"]}</strong></div>
                    <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div> <!-- No iframe inside initially -->
                </div>
                """ for char in characters
            )

            items_html += f"""
            <button class="collapsible">
                <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">

                <strong>{source_item} (Found in {len(characters)} Items)</strong>
            </button>
            <div class="content">
                {character_list_html if characters else "<p>No synth items used this.</p>"}
            </div>
            """

        return items_html
    synth_source_user_count = sum(len(users) for users in synth_sources.values())


    def generate_crafted_list_items(crafted_counters, crafted_users):
        items_html = ""

        for worn_category, counter in crafted_counters.items():
            if not counter:  # Skip empty categories
                continue
            
            unique_users = {char["name"]: char for item in counter for char in crafted_users.get(worn_category, {}).get(item, [])}
            # Skip categories with no users
            if not unique_users:
                continue

            # Collect all characters in this category
            category_users = []
            for item, count in counter.items():
                category_users.extend(crafted_users.get(worn_category, {}).get(item, []))

            # Skip categories with no users
            if not category_users:
                continue

            # Create the list of all users in this category
            character_list_html = "".join(
                f"""
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}
                        </a>
                    </div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div> <!-- No iframe inside initially -->
                </div>
                """ for char in category_users
            )

            # Create a collapsible button for each category
            items_html += f"""
            <button class="collapsible">
                <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                <strong>Crafted {worn_category} ({len(category_users)} users)</strong>
            </button>
            <div class="content">
                {character_list_html if category_users else "<p>No characters using crafted items in this category.</p>"}
            </div>
            """

        return items_html
    craft_user_count = len({char["name"] for users in crafted_users.values() for item_users in users.values() for char in item_users})
    craft_user_count = sum(len(users) for users in crafted_users.values())


    def generate_magic_list_items(magic_counters, magic_users):
        items_html = ""

        for worn_category, counter in magic_counters.items():
            if not counter:  # Skip empty categories
                continue

            # Collect unique characters in this category
            unique_users = {char["name"]: char for item in counter for char in magic_users.get(worn_category, {}).get(item, [])}

            # Skip categories with no users
            if not unique_users:
                continue

            # Create the list of all unique users in this category
            character_list_html = "".join(
                f"""
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}
                        </a>
                    </div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div> <!-- No iframe inside initially -->
                </div>
                """ for char in unique_users.values()
            )

            # Create a collapsible button for each category
            items_html += f"""
            <button class="collapsible">
                <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                <strong>Magic {worn_category} ({len(unique_users)} users)</strong>
            </button>
            <div class="content">
                {character_list_html if unique_users else "<p>No characters using magic items in this category.</p>"}
            </div>
            """

        return items_html

    # ✅ Count total **unique** magic item users across all categories
    magic_user_count = len({char["name"] for users in magic_users.values() for item_users in users.values() for char in item_users})
    magic_user_count = sum(len(users) for users in magic_users.values())


    def generate_rare_list_items(rare_counter, rare_users):
        items_html = ""

        for worn_category, counter in rare_counter.items():
            if not counter:  # Skip empty categories
                continue

            # Collect unique characters in this category
            unique_users = {char["name"]: char for item in counter for char in rare_users.get(worn_category, {}).get(item, [])}

            # Skip categories with no users
            if not unique_users:
                continue

            # Create the list of all unique users in this category
            character_list_html = "".join(
                f"""
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}
                        </a>
                    </div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div> <!-- No iframe inside initially -->
                </div>
                """ for char in unique_users.values()
            )

            # Create a collapsible button for each category
            items_html += f"""
            <button class="collapsible">
                <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                <strong>Rare {worn_category} ({len(unique_users)} users)</strong>
            </button>
            <div class="content">
                {character_list_html if unique_users else "<p>No characters using Rare items in this category.</p>"}
            </div>
            """

        return items_html

    # ✅ Count total **unique** rare item users across all categories
    rare_user_count = len({char["name"] for users in rare_users.values() for item_users in users.values() for char in item_users})
    rare_user_count = sum(len(users) for users in rare_users.values())

    def socket_html(sorted_runes, sorted_excluding_runes, all_other_items):
        just_socketed = []  # ✅ Holds ALL socketed items  
        just_socketed_excluding_runewords = []  # ✅ Should hold socketed items EXCEPT those inside runewords  

        def extract_element(item):
            if item.get('Title') == 'Rainbow Facet':
                element_types = ["fire", "cold", "lightning", "poison", "physical", "magic"]
                for element in element_types:
                    for prop in item.get('PropertyList', []):
                        if element in prop.lower():
                            return element.capitalize()
            return item.get('Title', 'Unknown')  # Use title if not "Rainbow Facet"


        # Define runes separately
        rune_names = {
            "El Rune", "Eld Rune", "Tir Rune", "Nef Rune", "Eth Rune", "Ith Rune", "Tal Rune", "Ral Rune", "Ort Rune", "Thul Rune", "Amn Rune", "Sol Rune",
            "Shael Rune", "Dol Rune", "Hel Rune", "Io Rune", "Lum Rune", "Ko Rune", "Fal Rune", "Lem Rune", "Pul Rune", "Um Rune", "Mal Rune", "Ist Rune",
            "Gul Rune", "Vex Rune", "Ohm Rune", "Lo Rune", "Sur Rune", "Ber Rune", "Jah Rune", "Cham Rune", "Zod Rune"
        }

        # Categorize worn slots
        def categorize_worn_slot(worn_category, text_tag):
            if worn_category in ["sweapon1", "weapon1", "sweapon2", "weapon2"]:
                if text_tag == "Arrows":
                    return "Arrows"
                elif text_tag == "Bolts":
                    return "Bolts"
                else:
                    return "Weapons and Shields"

            worn_category_map = {
                "ring1": "Rings", "ring2": "Rings",
                "body": "Armor",
                "gloves": "Gloves",
                "belt": "Belts",
                "helmet": "Helmets",
                "boots": "Boots",
                "amulet": "Amulets",
            }
            return worn_category_map.get(worn_category, "Other")  # Default to "Other"

        # Extract element type from Rainbow Facets
        def extract_element(item):
            if item.get('Title') == 'Rainbow Facet':
                element_types = ["fire", "cold", "lightning", "poison", "physical", "magic"]
                for element in element_types:
                    for prop in item.get('PropertyList', []):
                        if element in prop.lower():
                            return element.capitalize()
            return item.get('Title', 'Unknown')  # Use title if not "Rainbow Facet"

        # Function to process all characters from the single JSON file
        def process_all_items(json_file):
            with open(json_file, "r") as file:
                all_characters = json.load(file)  # ✅ Read all characters at once

            # Initialize counters
            all_items = []  
            socketed_items = []  
            items_excluding_runewords = []  
            facet_elements = defaultdict(list)
            
            shields_for_skulls = []
            weapons_for_skulls = []
            helmets_for_skulls = []
            armor_for_skulls = []
            
            jewel_counts = Counter()
            jewel_groupings = {"magic": [], "rare": []}

            # Process each character
            for char_data in all_characters:
                for item in char_data.get('Equipped', []):
                    
                    # Process Skull socketing locations
                    if item.get('Worn') == 'helmet':
                        if any(s.get('Title') == "Perfect Skull" for s in item.get('Sockets', [])):
                            helmets_for_skulls.append(item)
                    elif item.get('Worn') == 'body':
                        if any(s.get('Title') == "Perfect Skull" for s in item.get('Sockets', [])):
                            armor_for_skulls.append(item)
                    elif item.get('Worn') in ['weapon1', 'weapon2', 'sweapon1', 'sweapon2']:
                        is_shield = any("Block" in prop for prop in item.get('PropertyList', []))
                        for socketed_item in item.get('Sockets', []):
                            if socketed_item.get('Title') == "Perfect Skull":
                                if is_shield:
                                    shields_for_skulls.append(socketed_item)
                                else:
                                    weapons_for_skulls.append(socketed_item)

                    # Process Socketed Items
                    if item.get('SocketCount', '0') > '0':  # Check if item has sockets
                        all_items.append(item)
                        if item.get('QualityCode') != 'q_runeword':  # Exclude runewords
                            items_excluding_runewords.append(item)

                        for socketed_item in item.get('Sockets', []):
                            element = extract_element(socketed_item)
                            socketed_items.append(socketed_item)
                            facet_elements[element].append(socketed_item)

                            just_socketed.append(socketed_item)

                            # ✅ Extract QualityCode for categorization
                            quality_code = socketed_item.get('QualityCode', '')

                            # ✅ Separate Magic and Rare Jewels
                            if quality_code == "q_magic":
                                socketed_item["GroupedTitle"] = "Misc. Magic Jewels"
                            elif quality_code == "q_rare":
                                socketed_item["GroupedTitle"] = "Misc. Rare Jewels"
                            else:
                                socketed_item["GroupedTitle"] = socketed_item.get("Title", "Unknown")  # Default title

                            if item.get('QualityCode') != 'q_runeword':
                                items_excluding_runewords.append(socketed_item)
                                just_socketed_excluding_runewords.append(socketed_item)

                            if socketed_item.get('Title') == 'Rainbow Facet':
                                facet_elements[element].append(socketed_item)

            return (
                all_items, socketed_items, items_excluding_runewords,
                just_socketed, just_socketed_excluding_runewords, facet_elements,
                shields_for_skulls, weapons_for_skulls, helmets_for_skulls, armor_for_skulls
            )

        # Function to count item types
        def count_items_by_type(items):
            rune_counter = Counter()
            non_rune_counter = Counter()
            magic_jewel_counter = Counter()
            rare_jewel_counter = Counter()
            facet_counter = defaultdict(lambda: {"count": 0, "perfect": 0})

            for item in items:
                title = item.get('Title', 'Unknown')
                quality = item.get('QualityCode', '')

                if title in rune_names:  # ✅ Sort runes separately
                    rune_counter[title] += 1
                elif "Rainbow Facet" in title:  # ✅ Sort Rainbow Facets separately
                    element = extract_element(item)
                    facet_counter[element]["count"] += 1

                    # ✅ Check for perfect (both +5% and -5% properties)
                    properties = item.get('PropertyList', [])
                    if any("+5" in prop for prop in properties) and any("-5" in prop for prop in properties):
                        facet_counter[element]["perfect"] += 1
                elif quality == "q_magic":  # ✅ Track Magic Jewels with splash
                    has_splash = any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                    has_ias = any("attack speed" in prop.lower() for prop in item.get("PropertyList", []))
                    has_ed = any("enhanced damage" in prop.lower() for prop in item.get("PropertyList", []))
                    
                    magic_jewel_counter["Misc. Magic Jewels"] += 1
                    if has_splash:
                        magic_jewel_counter["splash"] += 1
                    if has_ias:
                        magic_jewel_counter["attack speed"] += 1
                    if has_ed:
                        magic_jewel_counter["enhanced damage"] += 1
                elif quality == "q_rare":  # ✅ Track Rare Jewels with splash
                    has_splash = any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                    rare_jewel_counter["Misc. Rare Jewels"] += 1
                    if has_splash:
                        rare_jewel_counter["splash"] += 1
                else:  # ✅ All other non-rune items
                    non_rune_counter[title] += 1

            return rune_counter, non_rune_counter, magic_jewel_counter, rare_jewel_counter, facet_counter

        # Example Usage
        json_file = "sc_ladder.json"
        all_items, socketed_items, *_ = process_all_items(json_file)
        just_socketed_runes, just_socketed_non_runes, *_ = count_items_by_type(socketed_items)


        def count_items_by_type(items):
            rune_counter = Counter()
            non_rune_counter = Counter()
            magic_jewel_counter = Counter()
            rare_jewel_counter = Counter()
            facet_counter = defaultdict(lambda: {"count": 0, "perfect": 0})
            skull_counter = Counter()

            for item in items:
                title = item.get('Title', 'Unknown')
                quality = item.get('QualityCode', '')

                if title in rune_names:  # ✅ Sort runes separately
                    rune_counter[title] += 1
                elif "Rainbow Facet" in title:  # ✅ Sort Rainbow Facets separately
                    element = extract_element(item)
                    facet_counter[element]["count"] += 1

                    # ✅ Check for perfect (both +5% and -5% properties)
                    properties = item.get('PropertyList', [])
                    if any("+5" in prop for prop in properties) and any("-5" in prop for prop in properties):
                        facet_counter[element]["perfect"] += 1
                elif quality == "q_magic":  # ✅ Track Magic Jewels with splash
                    has_splash = any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                    has_ias = any("attack speed" in prop.lower() for prop in item.get("PropertyList", []))
                    has_ed = any("enhanced damage" in prop.lower() for prop in item.get("PropertyList", []))
                    has_iassplash = any("attack speed" in prop.lower() for prop in item.get("PropertyList", [])) & any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                    has_iased = any("attack speed" in prop.lower() for prop in item.get("PropertyList", [])) & any("enhanced damage" in prop.lower() for prop in item.get("PropertyList", []))
                    magic_jewel_counter["Misc. Magic Jewels"] += 1
                    if has_splash:
                        magic_jewel_counter["splash"] += 1
                    if has_ias:
                        magic_jewel_counter["attack speed"] += 1
                    if has_ed:
                        magic_jewel_counter["enhanced damage"] += 1
                    if has_iassplash:
                        magic_jewel_counter["iassplash"] += 1
                    if has_iased:
                        magic_jewel_counter["iased"] += 1
#                    if has_splash & has_ias:
#                        magic_jewel_counter["splash"] += 1
                elif quality == "q_rare":  # ✅ Track Rare Jewels with splash
                    has_splash = any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                    has_ed = any("enhanced damage" in prop.lower() for prop in item.get("PropertyList", []))
                    rare_jewel_counter["Misc. Rare Jewels"] += 1
                    if has_splash:
                        rare_jewel_counter["splash"] += 1
                    if has_ed:
                        rare_jewel_counter["enhanced damage"] += 1
#                elif "Perfect Skull" in title:  # ✅ Sort Rainbow Facets separately
#                    skull_counter[title] += 1
                else:  # ✅ All other non-rune items
                    non_rune_counter[title] += 1

            return rune_counter, non_rune_counter, magic_jewel_counter, rare_jewel_counter, facet_counter #, skull_counter

        just_socketed_runes, just_socketed_non_runes, just_socketed_magic, just_socketed_rare, just_socketed_facets = count_items_by_type(socketed_items)
        just_socketed_excluding_runewords_runes, just_socketed_excluding_runewords_non_runes, just_socketed_excluding_runewords_magic, just_socketed_excluding_runewords_rare, just_socketed_excluding_runewords_facets = count_items_by_type(just_socketed_excluding_runewords)

        # Use .most_common() to sort data in descending order
        sorted_just_socketed_runes = just_socketed_runes.most_common()
        sorted_just_socketed_excluding_runewords_runes = just_socketed_excluding_runewords_runes.most_common()

        # Combine non-runes, magic, rare, and facets into a single list
        all_other_items = [
            *(f"{item}: {count}" for item, count in just_socketed_excluding_runewords_non_runes.items()),
            f"Misc. Magic Jewels: {just_socketed_excluding_runewords_magic['Misc. Magic Jewels']} ({just_socketed_excluding_runewords_magic['splash']} include melee splash, {just_socketed_excluding_runewords_magic['attack speed']} include IAS, {just_socketed_excluding_runewords_magic['enhanced damage']} include ED; of those, there are {just_socketed_excluding_runewords_magic['iassplash']} IAS/Splash and {just_socketed_excluding_runewords_magic['iased']} IAS/ED)",
            f"Misc. Rare Jewels: {just_socketed_excluding_runewords_rare['Misc. Rare Jewels']} ({just_socketed_excluding_runewords_rare['splash']} include melee splash, {just_socketed_excluding_runewords_rare['enhanced damage']} include ED)",
            *(f"Rainbow Facet ({element}): {counts['count']} ({counts['perfect']} are perfect)" for element, counts in just_socketed_excluding_runewords_facets.items()),
#            f"Perfect Skull:  (tacos)"

        ]
#        return sorted_just_socketed_runes, sorted_just_socketed_excluding_runewords_runes, all_other_items
        return (
            format_socket_html_runes(sorted_just_socketed_runes), 
            format_socket_html_runes(sorted_just_socketed_excluding_runewords_runes), 
            format_socket_html(all_other_items)
        )

    def format_socket_html(counter_data):
        """Formats socketed items as an HTML table or list."""
        if isinstance(counter_data, list):  # If it's a list, format as an unordered list
            items = "".join(f"<li>{item}</li>" for item in counter_data)
            return f"<ul>{items}</ul>"

        elif isinstance(counter_data, Counter):  # If it's a Counter, format as a table
            rows = "".join(f"<tr><td>{item}</td><td>{count}</td></tr>" for item, count in counter_data.items())
            return f"<table><tr><th>Item</th><th>Count</th></tr>{rows}</table>"

        elif isinstance(counter_data, dict):  # If it's a dict (e.g., facet counts), format as a list
            items = "".join(f"<li>{item}: {count['count']} ({count['perfect']} perfect)</li>" for item, count in counter_data.items())
            return f"<ul>{items}</ul>"

        return ""  # Return empty string if there's no data

    def format_socket_html_runes(counter_data):
        """Formats socketed items as an HTML table or list."""
        if isinstance(counter_data, list):  # If it's a list of tuples (like runes), format properly
            items = "".join(f"<li>{item}: {count}</li>" for item, count in counter_data)
            return f"<ul>{items}</ul>"

        elif isinstance(counter_data, Counter):  # If it's a Counter, format as a table
            rows = "".join(f"<tr><td>{item}</td><td>{count}</td></tr>" for item, count in counter_data.items())
            return f"<table><tr><th>Item</th><th>Count</th></tr>{rows}</table>"

        elif isinstance(counter_data, dict):  # If it's a dict (e.g., facet counts), format as a list
            items = "".join(f"<li>{item}: {count['count']} ({count['perfect']} perfect)</li>" for item, count in counter_data.items())
            return f"<ul>{items}</ul>"

        return ""  # Return empty string if there's no data


    # Merc things
    def map_readable_names(mercenary_type, worn_category):
        mercenary_mapping = {
            "Desert Mercenary": "Act 2 Desert Mercenary",
            "Rogue Scout": "Act 1 Rogue Scout",
            "Eastern Sorceror": "Act 3 Eastern Sorceror",
            "Barbarian": "Act 5 Barbarian"
        }
        worn_mapping = {
            "body": "Armor",
            "helmet": "Helmet",
            "weapon1": "Weapon",
            "weapon2": "Offhand"
        }
        readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
        readable_worn = worn_mapping.get(worn_category, worn_category)
        return readable_mercenary, readable_worn
    # Function to analyze mercenaries from a single JSON fileu
    def analyze_mercenaries(all_characters, runeword_counter, unique_counter, set_counter):
        """Analyzes mercenary equipment, updates global item counters, and tracks which mercs use which items."""
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))
        mercenary_names = Counter()
        merc_users = defaultdict(list)  # ✅ Track mercenary users for each item

        for char_data in all_characters:
            if not isinstance(char_data, dict):
                print(f"Skipping unexpected data format: {char_data}")
                continue  # Skip invalid entries

            mercenary = char_data.get("MercenaryType")
            if mercenary:
                readable_mercenary, _ = map_readable_names(mercenary, "")
                mercenary_counts[readable_mercenary] += 1

                merc_name = char_data.get("MercenaryName", "Unknown")
                mercenary_names[merc_name] += 1

                for item in char_data.get("MercenaryEquipped", []):
                    worn_category = item.get("Worn", "Unknown")
                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                    title = item.get("Title", "Unknown")
                    quality = item.get("QualityCode", "default")

                    # ✅ Add mercenary items to global counters
                    if quality == "q_runeword":
                        runeword_counter[title] += 1
                    elif quality == "q_unique":
                        unique_counter[title] += 1
                    elif quality == "q_set":
                        set_counter[title] += 1

                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1

                    # ✅ Track which characters' mercenaries are using each item
                    # ✅ Track which characters' mercenaries are using each item
                    merc_users[title.strip().lower()].append({
                        "Name": char_data.get("Name", "Unknown"),
                        "Class": char_data.get("Class", "Unknown"),
                        "Level": char_data.get("Stats", {}).get("Level", "N/A")
                    })

        return mercenary_counts, mercenary_equipment, mercenary_names, merc_users  # ✅ Return merc_users

           
    def generate_mercenary_report(all_characters, runeword_counter, unique_counter, set_counter):
        """Generates HTML report for mercenaries while ensuring their items are included in the item lists."""
        html_output = "<p><h2>Mercenary Analysis and Popular Equipment</h2></p>"

        # Mercenary type counts
        html_output += "<p><h3>Mercenary Type Counts</h3></p><ul>"
        for mercenary, count in mercenary_counts.items():
            html_output += f"<li>{mercenary}: {count}</li>"
        html_output += "</ul>"

        # Most Common Mercenary Names
        html_output += "<h3>Most Common Mercenary Names</h3><ul>"
        for name, count in mercenary_names.most_common(15):
            html_output += f"<li>{name}: {count}</li>"
        html_output += "</ul>"

        # Popular Equipment by Mercenary Type
        html_output += "<p><h3>Popular Equipment by Mercenary Type</h3></p>"
        for mercenary, categories in mercenary_equipment.items():
            html_output += f"<div class='row'><p><strong>{mercenary}</strong></p>"
            for worn_category, items in categories.items():
                html_output += f"<div class='merccolumn'><strong>Most Common {worn_category}s:</strong>"
                html_output += "<ul>"
                top_items = items.most_common(15)
                for title, count in top_items:
                    html_output += f"<li>{title}: {count}</li>"
                html_output += "</ul></div>"
            html_output += "</div>"

        return html_output

    # ✅ Load the consolidated JSON file
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)


    # ✅ Call analyze_mercenaries and store its results
    mercenary_counts, mercenary_equipment, mercenary_names, merc_users = analyze_mercenaries(
        all_characters, runeword_counter, unique_counter, set_counter
    )

    # ✅ Extract all items used by mercenaries (after calling analyze_mercenaries)
    merc_used_items = set()
    for categories in mercenary_equipment.values():  # Iterate over mercenary types
        for worn_category, items in categories.items():
            merc_used_items.update(items.keys())  # Add all item names to the set

    # Analyze mercenaries while updating item counts
    html_output = generate_mercenary_report(all_characters, runeword_counter, unique_counter, set_counter)

    # Now, the used item lists include mercenary items!

    # Generate the report
#    html_output = generate_mercenary_report(all_characters)

    used_runewords = {item[0] for item in all_runewords}
    used_uniques = {item[0] for item in all_uniques_all}
    used_set_items = {item[0] for item in all_set}
    all_the_items = items_list.all_the_items
    # Ensure `items_list.all_the_items` exists
    try:
        all_the_items = items_list.all_the_items  # ✅ Ensure this is defined
        unused_runewords = {rw.strip().lower() for rw in all_the_items["all_the_runewords"]} - {rw.strip().lower() for rw in used_runewords}
        unused_uniques = {rw.strip().lower() for rw in all_the_items["all_the_uniques"]} - {rw.strip().lower() for rw in used_uniques}
        unused_set_items = {rw.strip().lower() for rw in all_the_items["all_the_sets"]} - {rw.strip().lower() for rw in used_set_items}
    except AttributeError as e:
        print("Error: items_list is not defined or missing required keys.", e)
        unused_runewords = unused_uniques = unused_set_items = set()  # ✅ Prevent crashes

    print("Unused Runewords:", unused_runewords)
    print("Unused Unique Items:", unused_uniques)
    print("Unused Set Items:", unused_set_items)

    # ✅ Ensure merc_used_items is case-insensitive
    merc_used_items = {item.strip().lower() for item in merc_used_items}

    def format_unused_items(items, merc_used_items, merc_users):
        """Converts a set of unused items into an HTML list, with expandy sections for mercs using them."""
        if not items:
            return "<p>No unused items found.</p>"

        html_output = "<ul>"
        
        for item in sorted(items):
            formatted_item = item.strip().lower()
            is_merc_only = formatted_item in merc_used_items
            merc_list = merc_users.get(formatted_item, [])

            # ✅ Generate character list HTML for merc users
            merc_character_html = "".join(
                f"""
                <div class="character-info">
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["Name"]}" target="_blank">
                            {char["Name"]}
                        </a>
                    </div>
                    <div>Level {char["Level"]} {char["Class"]}</div>
                    <div class="hover-trigger" data-character-name="{char["Name"]}"><!-- Armory Quickview--></div>
                </div>
                <div class="character">
                    <div class="popup hidden"></div>
                </div>
                """
                for char in merc_list
            )

            # ✅ Add collapsible button for mercs
            merc_html_section = ""
            if merc_list:
                merc_html_section = f"""
                <button class="collapsible">
                    <img src="icons/open-grey.png" alt="Expand Mercenaries" class="icon-small open-icon hidden">
                    <img src="icons/closed-grey.png" alt="Collapse Mercenaries" class="icon-small close-icon">
                    <p>Characters whose mercs use {item}</p>
                </button>
                <div class="content">
                    {merc_character_html if merc_character_html else "<p>No mercenaries using this item.</p>"}
                </div>
                """

            # ✅ Add item to list with (only used on mercenaries) if applicable
            html_output += f"""
            <li>
                <strong>{item} </strong>
                <span style='color:gray;'>{'(only used on mercenaries)' if is_merc_only else ''}</span>
                {merc_html_section}
            </li>
            """

        html_output += "</ul>"
        return html_output
    
    merc_used_items = set(merc_users.keys())  # ✅ All lowercase and stripped
    # ✅ Generate updated HTML
    unused_runewords_html = format_unused_items(unused_runewords, merc_used_items, merc_users)
    unused_uniques_html = format_unused_items(unused_uniques, merc_used_items, merc_users)
    unused_set_items_html = format_unused_items(unused_set_items, merc_used_items, merc_users)

    # Generating the HTML for the results
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="Ever wonder how many Shako's are in use? Or what the most popular Sorc skills are? This site provides information about class build trends and item details from characters on the current Path of Diablo (PoD) ladder. An alternative to the old analytics site we all know and love.">
        <meta name="keywords" content="path of diablo, builds, stats, statistics, data, analysis, analytics">
        <meta name="robots" content="index, follow">
        <title>PoD Softcore Stats</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        
        
    </head>
    <body class="special-background">
<!--    
        <div class="is-clipped">
        <nav class="navbar is-fixed-top is-dark" style="height: 50px;">

            <div class="navbar-brand">
                <a class="" href="https://pathofdiablo.com/p/"><img src="icons/pod.ico" alt="Path of Diablo: Web Portal" width="48" height="48" class="is-48x48" style="max-height: none;"></a>
                <div class="navbar-burger burger" data-target="podNavbar"><span></span><span></span><span></span>
                </div>
            </div>
            <div id="podNavbar" class="navbar-menu">
                <div class="navbar-start">
                    <a class="navbar-item" href="https://beta.pathofdiablo.com/trade-search">Trade</a>
                    <a class="navbar-item" href="https://pathofdiablo.com/p/?servers">Servers</a>
                    <a class="navbar-item" href="https://beta.pathofdiablo.com/ladder">Ladder</a>
                    <a class="navbar-item" href="https://beta.pathofdiablo.com/public-games">Public Games</a>
                    <a class="navbar-item" href="https://beta.pathofdiablo.com/runewizard">Runewizard</a>
                    <a class="navbar-item" href="https://pathofdiablo.com/p/armory">Armory</a>
                    <a class="navbar-item" href="https://build.pathofdiablo.com">Build Planner</a>
                    <a class="navbar-item" href="https://pathofdiablo.com/p/?live" style="width: 90px;"><span><img src="https://beta.pathofdiablo.com/images/twitchico.png"></span></a>
                </div>
                <div class="navbar-end">

                    <div class="navbar-start">	
                    <a class="navbar-item-right" href="https://beta.pathofdiablo.com/my-toons">Character Storage</a>
                    <!--<a class="navbar-item" href="https://pathofdiablo.com/p/?ticket"><span><svg class="svg-inline--fa fa-exclamation-circle fa-w-16" aria-hidden="true" data-prefix="fas" data-icon="exclamation-circle" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" data-fa-i2svg=""><path fill="currentColor" d="M504 256c0 136.997-111.043 248-248 248S8 392.997 8 256C8 119.083 119.043 8 256 8s248 111.083 248 248zm-248 50c-25.405 0-46 20.595-46 46s20.595 46 46 46 46-20.595 46-46-20.595-46-46-46zm-43.673-165.346l7.418 136c.347 6.364 5.609 11.346 11.982 11.346h48.546c6.373 0 11.635-4.982 11.982-11.346l7.418-136c.375-6.874-5.098-12.654-11.982-12.654h-63.383c-6.884 0-12.356 5.78-11.981 12.654z"></path></svg><!-- <i class="fas fa-exclamation-circle"></i> /span></a> 
                    </div>
                </div>
        </nav>  
-->    

        <!--<div class="top-buttons">
            <a href="Home.html" class="top-button" onclick="setActive('Home')">Home</a>
            <div class="split-button">
                <button id="SC" class="split-button-option" onclick="setActive('SC')">SC</button>
                <button id="HC" class="split-button-option" onclick="setActive('HC')">HC</button>
            </div>
            <a href="Amazon.html" class="top-button">Amazon</a>
            <a href="Assassin.html" class="top-button">Assassin</a>
            <a href="Barbarian.html" class="top-button">Barbarian</a>
            <a href="Druid.html" class="top-button">Druid</a>
            <a href="Necromancer.html" class="top-button">Necromancer</a>
            <a href="Paladin.html" class="top-button">Paladin</a>
            <a href="Sorceress.html" class="top-button">Sorceress</a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button" target="_blank">About</a>
        </div> -->

        
        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>
        
<div class="main page-intro">
        <h1>PoD SOFTCORE LADDER TOP 1,000 CLASS DISTRIBUTION </h1>
        <h2>Looking at the class distribution for the ladders top 1,000 characters shows which classes are played for longer, a measure of which classes are more popular in the endgame</h2>
        <!-- Embed the Plotly pie chart -->
    <!--     <h2>Pick a class below for more detail</h2>-->
    <!--     <iframe src="cluster_analysis_report.html"></iframe>  -->
        <div>
            <img src="charts/1kclass_distribution.png">
        </div>
       <h2>Since there are class ladders in addition to the top 1,000, and many ranked characters do not appear in the top 1k, they are included below and in the rest of the Trends reporting to get as large a data set as possible when looking at item & equipment usage and skill distribution within classes</h2>
       <h1>PoD SOFTCORE STATS, ALL RANKED LADDER CHARACTERS CLASS DISTRIBUTION  </h1>
        <!-- Embed the Plotly pie chart -->
    <!--     <h2>Pick a class below for more detail</h2>-->
    <!--     <iframe src="cluster_analysis_report.html"></iframe>  -->
        <div>
            <img src="charts/class_distribution.png">
        </div>
        <h3>THESE PAGES INCLUDE DATA FROM ALL AVAILABLE RANKED LADDER CHARACTERS (THE TOP 1,000 AS WELL AS THE TOP 200 FROM EACH CLASS)</h3>
<!--        <h3>UNLESS STATED OTHERWISE, OTHER PAGE STATS AND DATA ARE FROM THE TOP 200 CHARACTERS OF THE RELEVANT CLASS OR CLASSES</h3> -->
    <hr>
        <h3>Class and special pages have taken character data and separated it into probable builds. As such, the groupings and associated data
            will change over time to reflect what is currently accurate.
            <br><br>
            Looking at class and build pages, what you see and what it means:</h3>
        <div>
            <img src="charts/build-pages-legend.png">
        </div>
        <h3>Looking at skills you can assume that:</h3>
        <ul style="padding-left:20px">
         <li>If the first number is 50%, then half of the characters fall into that "build"</li>
         <li>If the percent bar following a skill is 100% then every character in that group has points in that skill</li>
         <li>If the percent is 100% and the total points is high that skill is likely a main skill or synergy </li>
         <li>If the percent is 100% but the total is low that skill is likely one-point-wonder like Hydra and Whirlwind or just a prerequisite </li>
         </ul>
         </h3>
         

    <br>
        <!-- Moved the Plotly scatter plot to the bottom -->
        <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>
        <hr> 
        <h1>Non-Class specific reporting</h1>
<h3>Most and Least Used Runewords, Uniques, and Set items currently equipped by characters</h3>

<button type="button" class="collapsible runewords-button">
    <img src="icons/Runewords_click.png" alt="Runewords Open" class="icon open-icon hidden">
    <img src="icons/Runewords.png" alt="Runewords Close" class="icon close-icon">
<!--    <strong>Runewords</strong> -->
</button>
<div class="content">
    <div id="runewords" class="container">
        <div class="column">
            <h3>Most Used Runewords:</h3>
            <ul id="most-popular-runewords">
                {most_popular_runewords}
            </ul>
        </div>
        <div class="column">
            <h3>Least Used Runewords:</h3>
            <ul id="least-popular-runewords">
                {least_popular_runewords}
            </ul>
        </div>
    </div>


    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="All Runewords Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Runewords Close" class="icon-small close-icon">
        <strong>ALL Runewords</strong>
    </button>

    <div class="content">
        <div id="allrunewords">
            {all_runewords}
        </div>
    </div>
</div>

<br>
<button type="button" class="collapsible uniques-button">
    <img src="icons/Uniques_click.png" alt="Uniques Open" class="icon open-icon hidden">
    <img src="icons/Uniques.png" alt="Uniques Close" class="icon close-icon">
<!--    <strong>Uniques</strong>-->
</button>    
<div class="content">   
    <div id="uniques" class="container">
        <div class="column">
            <h3>Most Used Uniques:</h3>
            <ul id="most-popular-uniques">
                {most_popular_uniques}
            </ul>
        </div>
        <div class="column">
            <h3>Least Used Uniques:</h3>
            <ul id="least_popular_uniques">
                {least_popular_uniques}
            </ul>
        </div>
    </div>
    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="All Uniques Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Uniques Close" class="icon-small close-icon">
        <strong>ALL Uniques</strong>
    </button>

    <div class="content">
        <div id="alluniques">
            {all_uniques}
        </div>
    </div>

</div>

<br>
<button type="button" class="collapsible sets-button">
    <img src="icons/Sets_click.png" alt="Sets Open" class="icon open-icon hidden">
    <img src="icons/Sets.png" alt="Sets Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">  
    <div id="sets" class="container">
        <div class="column">
            <h3>Most Used Set Items:</h3>
            <ul id="most-popular-set-items">
                {most_popular_set_items}
            </ul>
        </div>
        <div class="column">
            <h3>Least Used Set Items:</h3>
            <ul id="least_popular_set_items">
                {least_popular_set_items}
            </ul>
        </div>
    </div>
    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="All Set Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Set Close" class="icon-small close-icon">
        <strong>ALL Set</strong>
    </button>

    <div class="content">
        <div id="allset">
            {all_set}
        </div>
    </div>
</div>
<br>
<hr>

        <br>

        <h1>Mercenary reporting</h1>
        <h3>Mercenary counts and Most Used Runewords, Uniques, and Set items equipped</h3>

        <button type="button" class="collapsible">
            <img src="icons/Merc_click.png" alt="Merc Details Open" class="icon open-icon hidden">
            <img src="icons/Merc.png" alt="Merc Details Close" class="icon close-icon">
<!--            <strong>Mercenary Details</strong> -->
        </button>
        <div class="content">
        <div id="mercequips">
            {html_output}
        </div>
        </div>
        <br>
    
        <br>
        <hr>
        <h1>Specialty Searches, Items</h1>
        <h2>Synth reporting</h2>
        <h2>{synth_user_count} Characters with Synthesized items equipped</h2>
        <h3>This is base synthesized items</h3>
<button type="button" class="collapsible sets-button">
    <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
    <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">  
        <div id="special">
            {all_synth}
        </div>
    </div>

        <h2>{synth_source_user_count} Synthesized FROM listings</h2>
        <h3>This shows where propertied an item are showing up in other items. If you wanted to see where the slow from Kelpie or the Ball light from Ondal's had popped up, this is where to look </h3>
<button type="button" class="collapsible sets-button">
    <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
    <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">  
        <div id="special">
            {synth_source_data}
        </div>
    </div>


        <br>

        <h2>Craft reporting</h2>
        <h3>{craft_user_count} Characters with crafted items equipped</h3>

<button type="button" class="collapsible sets-button">
    <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
    <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">  
        <div id="special">
            {all_crafted}
        </div>
    </div>

<br>

<br>
        <h2>Magic reporting</h2>
        <h3>{magic_user_count} Characters with Magic items equipped</h3>

<button type="button" class="collapsible sets-button">
    <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
    <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">  
        <div id="special">
            {all_magic}
        </div>
    </div>

<br>

        <h2>Rare reporting</h2>
        <h3>{rare_user_count} Characters with rare items equipped</h3>

<button type="button" class="collapsible sets-button">
    <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
    <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">  
        <div id="special">
            {all_rare}
        </div>
    </div>

<br>

        <h2>Socketable reporting</h2>
        <h3>What are people puting in sockets</h3>

<button type="button" class="collapsible sets-button">
    <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
    <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">  
        <h2>Socketed Runes Count</h2>
        <h3>Includes Only Character Data, No Mercs</h3>
    <div id="special"  class="container">
<br>
        <div class="column">
            <!-- Left Column -->
                <h2>Most Common Runes <br>(Including Runewords)</h2>
            <ul id="sorted_just_socketed_runes"
                {sorted_just_socketed_runes}
            </ul>
            </div>

            <!-- Right Column -->
            <div class="column">
                <h2>Most Common Runes <br>(Excluding Runewords)</h2>
            <ul id="sorted_just_socketed_excluding_runewords_runes">
                {sorted_just_socketed_excluding_runewords_runes}
            </ul>
            </div>
        </div>

        <div>
            <h2>Other Items Found in Sockets</h2>
        <h3>Includes Only Character Data, No Mercs</h3>
            {all_other_items}
        </div>
    </div>
<br>
            <h2>Unused Items</h2>
            <h3>Some items get no love at the top of the ladder</h3>
<button type="button" class="collapsible sets-button">
    <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
    <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
<!--    <strong>Sets</strong>-->
</button>  
<div class="content">
    <!-- Runewords -->
    <button class="collapsible"> 
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
        <strong>Unused Runewords</strong>
    </button>
    <div class="content">{unused_runewords}</div>

    <!-- Uniques -->
    <button class="collapsible"> 
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
        <strong>Unused Unique Items</strong>
    </button>
    <div class="content">{unused_uniques}</div>

    <!-- Set Items -->
    <button class="collapsible"> 
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
        <strong>Unused Set Items</strong>
    </button>
    <div class="content">{unused_set_items}</div>
</div>
<br>
<hr>

<br>

        <h1>Specialty Searches, Character Builds</h1>
        <h2>Special builds and custom querries that don't fit in class specific pages</h2>
        <h2>Iron Jang Bong & Warpspear</h2>
        <a href="Bong_and_Warpspear.html"> <img src="icons/Special.png" alt="Iron Jang Bong & Warpspear" style="width:300px;height:50px;" class="collapsible icon"></a>
        <br>
        <h2>Unique Arrows & Bolts</h2>
        <a href="Unique_Bolts_and_Arrows.html"> <img src="icons/Special.png" alt="Unique Arrows & Bolts" style="width:300px;height:50px;" class="collapsible icon"></a>
        <br>
        <h2>Non-Amazon Bow Users</h2>
        <a href="Notazons.html"> <img src="icons/Special.png" alt="Non-Amazon Bow Users" style="width:300px;height:50px;" class="collapsible icon"></a>
        <br>
        <h2>Dual Offensive Aura Items Equipped</h2>
        <a href="2AuraItems.html"> <img src="icons/Special.png" alt="Dual Offensive Aura Items Equipped" style="width:300px;height:50px;" class="collapsible icon"></a>
        <br>
        <h2>Dashing Strikers</h2>
        <a href="Dashadin.html"> <img src="icons/Special.png" alt="Dashing Strikers" style="width:300px;height:50px;" class="collapsible icon"></a>
        <br>
        <h2>Possibly Chargers</h2>
        <a href="Charge.html"> <img src="icons/Special.png" alt="Possibly Chargers" style="width:300px;height:50px;" class="collapsible icon"></a>
        <br>
        <br>
        <hr>
        <h1>Specialty Searches, Misc. Data</h1>
{fun_facts_html}
<br>
<br>        
<br>
<br>


        </div>
        <div class="footer">
        <p>PoD data current as of {timeStamp}</p>
        </div>





<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}


//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}

document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});

document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});

document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>



    </body>
    </html>
    """

    socketed_runes_html, socketed_excluding_runes_html, other_items_html = socket_html(
        sorted_just_socketed_runes, 
        sorted_just_socketed_excluding_runewords_runes, 
        all_other_items
    )

    filled_html_content = f"""{html_content}""".replace(
        "{most_popular_runewords}", generate_list_items(most_common_runewords)
    ).replace(
        "{most_popular_uniques}", generate_list_items(most_common_uniques)
    ).replace(
        "{most_popular_set_items}", generate_list_items(most_common_set_items)
    ).replace(
        "{least_popular_runewords}", generate_list_items(least_common_runewords)
    ).replace(
        "{least_popular_uniques}", generate_list_items(least_common_uniques)
    ).replace(
        "{least_popular_set_items}", generate_list_items(least_common_set_items)
    ).replace( 
        "{all_runewords}", generate_all_list_items(all_runewords, all_characters)
    ).replace(
        "{all_uniques}", generate_all_list_items(all_uniques, all_characters)
    ).replace(
        "{all_set}", generate_all_list_items(all_set, all_characters)
    ).replace(
        "{all_synth}", generate_synth_list_items(synth_counter, synth_users)
    ).replace(
        "{timeStamp}", timeStamp
    ).replace(
        "{synth_user_count}", str(synth_user_count)
    ).replace(
        "{all_crafted}", generate_crafted_list_items(crafted_counters, crafted_users)
    ).replace(
        "{craft_user_count}", str(craft_user_count)
    ).replace(
        "{synth_source_data}", generate_synth_source_list(synth_sources)
    ).replace(
        "{synth_source_user_count}", str(synth_source_user_count)
    ).replace(
        "{all_magic}", generate_magic_list_items(magic_counters, magic_users)
    ).replace(
        "{magic_user_count}", str(magic_user_count)
    ).replace(
        "{all_rare}", generate_rare_list_items(rare_counters, rare_users)
    ).replace(
        "{rare_user_count}", str(rare_user_count)
    ).replace(
        "{sorted_just_socketed_runes}", socketed_runes_html  # ✅ Correctly insert formatted HTML
    ).replace(
        "{sorted_just_socketed_excluding_runewords_runes}", socketed_excluding_runes_html
    ).replace(
        "{all_other_items}", other_items_html
    ).replace(
        "{fun_facts_html}", fun_facts_html
    ).replace(
        "{unused_runewords}", unused_runewords_html
    ).replace(
        "{unused_uniques}", unused_uniques_html
    ).replace(
        "{unused_set_items}", unused_set_items_html
    ).replace(
        "{html_output}", html_output
    )


    print("Runewords:", sum(runeword_counter.values()))
    print("Uniques:", sum(unique_counter.values()))
    print("Set items:", sum(set_counter.values()))
#    print("Synth:", sum(synth_counter[worn_category][title] for worn_category in synth_counter for title in synth_counter[worn_category]))
 #   print("Crafted:", sum(crafted_counters[worn_category][title] for worn_category in crafted_counters for title in crafted_counters[worn_category]))
 #   print("Magic:", sum(magic_counters[worn_category][title] for worn_category in magic_counters for title in magic_counters[worn_category]))
 #   print("Rare:", sum(rare_counters[worn_category][title] for worn_category in rare_counters for title in rare_counters[worn_category]))

#    template = Template(html_content)
#    html_content = template.render(html_output=html_output)  # Pass sorted clusters to the template

    # Write the filled HTML content to a file
    with open('pod-stats/Home.html', 'w') as file:
        file.write(filled_html_content)
    with open('pod-stats/index.html', 'w') as file:
        file.write(filled_html_content)

    print("HTML file generated successfully.")

#MakeHome()

###############################################################
#
# Get dashing strike builds
#
# Item counts look funny
import json
import pandas as pd

def GetDashers():
    icons_folder = "icons"
    what_class = "Dashadin"
    howmany_skills = 4
    search_skill = "Dashing Strike"
    skill_threshold = 10

    # Load the consolidated JSON file
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)

    # Filter characters who meet the skill threshold
    filtered_characters = []
    
    for char_data in all_characters:
        has_high_charge = False
        
        for tab in char_data.get('SkillTabs', []):
            for skill in tab.get('Skills', []):
                if skill["Name"] == search_skill and skill["Level"] > skill_threshold:
                    has_high_charge = True
                    break  # Stop checking once condition is met
        
        if has_high_charge:
            filtered_characters.append(char_data)

        def map_readable_names(mercenary_type, worn_category=""):
            mercenary_mapping = {
                "Desert Mercenary": "Act 2 Desert Mercenary",
                "Rogue Scout": "Act 1 Rogue Scout",
                "Eastern Sorceror": "Act 3 Eastern Sorceror",
                "Barbarian": "Act 5 Barbarian"
            }
            worn_mapping = {
                "body": "Armor",
                "helmet": "Helmet",
                "weapon1": "Weapon",
                "weapon2": "Offhand"
            }
            readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
            readable_worn = worn_mapping.get(worn_category, worn_category)
            return readable_mercenary, readable_worn

    # Process data from filtered characters
    def load_data(filtered_characters):
        all_data = []
        
        quality_colors = {
            "q_runeword": "#edcd74",
            "q_unique": "#edcd74",
            "q_set": "#45a823",
            "q_magic": "#7074c9",
            "q_rare": "yellow",
            "q_crafted": "orange"
        }

        def map_readable_names(mercenary_type, worn_category=""):
            mercenary_mapping = {
                "Desert Mercenary": "Act 2 Desert Mercenary",
                "Rogue Scout": "Act 1 Rogue Scout",
                "Eastern Sorceror": "Act 3 Eastern Sorceror",
                "Barbarian": "Act 5 Barbarian"
            }
            worn_mapping = {
                "body": "Armor",
                "helmet": "Helmet",
                "weapon1": "Weapon",
                "weapon2": "Offhand"
            }
            readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
            readable_worn = worn_mapping.get(worn_category, worn_category)
            return readable_mercenary, readable_worn

        for char_data in filtered_characters:
            skill_data = {
                'Name': char_data.get('Name', 'Unknown'),
                'Class': char_data.get('Class', 'Unknown'),
                'Level': char_data.get('Stats', {}).get('Level', 'Unknown'),
            }
            
            # Extract and sort skills
            skills = []
            for tab in char_data.get('SkillTabs', []):
                for skill in tab.get('Skills', []):
                    skill_name = skill['Name']
                    skill_level = skill['Level']
                    skill_data[skill_name] = skill_level  # ✅ Creates a separate column for each skill
                    skills.append((skill_name, skill_level))
            
            skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
            skill_data['Skills'] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])

            # Extract equipment details
            equipment_titles = {}
            for item in char_data.get('Equipped', []):
                worn_category = item.get('Worn', 'Unknown')
                title = item.get('Title', 'Unknown')
                quality_code = item.get('QualityCode', 'default')
                color = quality_colors.get(quality_code, "white")
                colored_title = f"<span style='color: {color};'>{title}</span>"

                category_map = {
                    "ring1": "Ring", "ring2": "Ring",
                    "sweapon1": "Left hand", "weapon1": "Left hand",
                    "sweapon2": "Offhand", "weapon2": "Offhand",
                    "body": "Armor", "gloves": "Gloves", "belt": "Belt",
                    "helmet": "Helmet", "amulet": "Amulet"
                }
                
                worn_category = category_map.get(worn_category, worn_category)

                if worn_category not in equipment_titles:
                    equipment_titles[worn_category] = {}

                equipment_titles[worn_category][colored_title] = equipment_titles[worn_category].get(colored_title, 0) + 1

            skill_data['Equipment'] = ", ".join(
                f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                for worn, titles in equipment_titles.items()
                for title, count in titles.items()
            )

            # Extract mercenary details
            mercenary_type = char_data.get("MercenaryType", "No mercenary")
            readable_mercenary, _ = map_readable_names(mercenary_type)
            mercenary_equipment = ", ".join(
                [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
            ) if char_data.get("MercenaryEquipped") else "No equipment"

            skill_data['Mercenary'] = readable_mercenary
            skill_data['MercenaryEquipment'] = mercenary_equipment

            all_data.append(skill_data)

        return pd.DataFrame(all_data).fillna(0)

    # Load the data
    df = load_data(filtered_characters)
#    return df

    # Define skill columns (exclude non-skill columns)
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment']]
    df = pd.DataFrame(df)  # Ensure it's a DataFrame
#    print("DataFrame Columns:", df.columns.tolist())  # List column names
#    print("First Few Rows:\n", df.head())  # Show first few rows

#    print(df[['Name', 'Class']].head())  # Check Class column contents
    
    # Determine number of clusters dynamically
    unique_classes = df['Class'].nunique()  # 🔹 Count unique classes
    print(f"🔍 Unique Classes Found: {unique_classes}")

    # Ensure at least 2 clusters for meaningful results
    num_clusters = max(unique_classes, 2)  # 🔹 Avoids issues with a single class
    print(f"📊 Setting n_clusters = {num_clusters}")

    # Perform PCA
    pca = PCA(n_components=2)
    reduced_data = pca.fit_transform(df[skill_columns])

    # Perform KMeans clustering using dynamic `num_clusters`
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    df['Cluster'] = kmeans.fit_predict(df[skill_columns])

    # Calculate the average points invested in skills per cluster
    df['Total_Points'] = df[skill_columns].sum(axis=1)
    cluster_averages = df.groupby('Cluster')['Total_Points'].mean().reset_index()
    cluster_averages.columns = ['Cluster', 'Avg_Points']

    # Merge the averages back into the main DataFrame
    df = pd.merge(df, cluster_averages, on='Cluster')

    # Get skill averages per cluster
    skill_averages = df.groupby('Cluster')[skill_columns].mean()

    # Identify the top skills per cluster with their average points
    top_skills_with_avg = skill_averages.apply(lambda x: [(skill, round(x[skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)


    # Calculate the correct percentages for each cluster
    cluster_counts = df['Cluster'].value_counts(normalize=True) * 100
    df['Percentage'] = df['Cluster'].map(cluster_counts)

    # Map clusters to meaningful names (top skills with average points)
    cluster_labels = {i: ", ".join([f"{skill} ({avg})" for skill, avg in skills]) for i, skills in enumerate(top_skills_with_avg)}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Updated HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ what_class }} Analysis Report</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

    </head>
    <body class="not-main">
        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>

        <h1>{{ what_class }} Softcore Skill Distribution </h1>
        <div class="summary-container">
                        

        <h3>This group includes anyone with 10 or more points in Dashing Strike</h3>
        <p class="indented-skills">Popular builds include:<br>{{ summary_label }} </p>

        <hr>
        {% for clusters, data in clusters.items() %}
        <!--<h2>{{ data['label'] }}</h2>
        <p class="indented-skills"><strong>Other Skills:<br></strong> {{ data['other_skills'] }}</p> -->
        <div class="class-intro">
        <div id="skills" class="skills-container">
            <div class="column">
                <ul id="most-popular-skills">
                    <h2>{{ data['label'] }}</h2>
                </ul>
            </div>
<!--            <div class="column">
                <ul id="other-skills">
                    <h2>Other common skills in this group:</h2> {{ data['other_skills'] }}
                </ul>
            </div> -->
        </div>
            <button type="button" class="collapsible small-collapsible">

        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>All Skills</strong></button>
            <div class="content">
                <div>{{ data['remaining_skills_with_icons'] }}</div>
            </div>

            <button type="button" class="collapsible small-collapsible">

        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>Most Common Equipment:</strong></button>
            <div class="content">
                <div>{{ data['top_equipment'] }}</div>
            </div>
<!--        
            <button type="button" class="collapsible small-collapsible">
 
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>ALL Equipment:</strong></button>
            <div class="content">
                <div>{{ data['equipment_counts'] }}</div>
            </div>
-->
            <button type="button" class="collapsible small-collapsible">

        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>{{ data['character_count'] }} Characters in this cluster:</strong>
        </button>
        <div class="content2">
{% for character in data['characters'] %}
<!--
<div class="character-container {% if loop.index is even %}char1{% else %}char2{% endif %}">
-->
<div class="character-container char2">
    <div class="character-info">
        <div class="character-link"><strong>Name: <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}
            </a></strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="hover-trigger" data-character-name="{{ character['name'] }}">
            <!-- Armory Quickview -->
        </div>
    </div>

    <div class="character">
        <div class="popup hidden"></div> <!-- No iframe inside initially -->
    </div>

    <p><strong>Skills:<br></strong> {{ character['skills'] }}</p>
    <p><strong>Equipment:<br></strong> {{ character['equipment'] }}</p>
    <p><strong>Mercenary:<br></strong> {{ character['mercenary'] }} - {{ character['mercenary_equipment'] }}</p>

    <div class="character-section" data-character-name="{{ character['name'] }}"></div>
</div>
<hr color="#141414">
<br>
{% endfor %}
            <br>
            </div>
            </div>
<!--            <hr width="90%"> -->
            <br>
            {% endfor %}
            </div>
        <!--    <h3>Top 5 Most Popular {{ what_class }} Skills:</h3>
        <ul>
        </ul>

        <h3>Bottom 5 Least Popular {{ what_class }} Skills:</h3>
        <ul>
        </ul> -->
        <br><br><br>
        <!-- Embed the Plotly pie chart -->
        <div>
            <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
        </div>

        <!-- Embed the Plotly scatter plot -->
        <div>
            <img src="charts/{{ what_class }}-clusters_with_avg_points.png" alt="{{ what_class }} Skill Clusters Scatter Plot">
        </div>
        <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>
            <div class="footer">
            <p>PoD data current as of {{ timeStamp }}</p>
            </div>
        



<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}


//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}


document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});

document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});

document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>


 





    </body>
    </html>
    """

    def analyze_mercenaries(characters):
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        for char_data in characters:
            if not isinstance(char_data, dict):
                print(f"Skipping unexpected data format: {char_data}")
                continue  # Skip invalid entries

            mercenary = char_data.get("MercenaryType")
            if mercenary:
                readable_mercenary, _ = map_readable_names(mercenary, "")
                mercenary_counts[readable_mercenary] += 1

                for item in char_data.get("MercenaryEquipped", []):
                    worn_category = item.get("Worn", "Unknown")
                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                    title = item.get("Title", "Unknown")
                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1

        return mercenary, mercenary_counts, mercenary_equipment

    # Assuming df is your DataFrame and skill_columns contains the column names for the skills

    # Calculate the total usage of each skill across all clusters
    total_skill_usage = df[skill_columns].sum()

    # Sort skills by total usage in descending order
    most_used_skills = total_skill_usage.sort_values(ascending=False)

    # Sort skills by total usage in ascending order
    least_used_skills = total_skill_usage.sort_values(ascending=True)

    # Extract the top 5 most used skills
    top_5_most_used_skills = most_used_skills.head(5)

    # Extract the bottom 5 least used skills
    bottom_5_least_used_skills = least_used_skills.head(5)


    # Calculate the percentage of characters that have invested in each skill within the cluster
    skill_percentages = df[skill_columns].astype(bool).groupby(df['Cluster']).mean() * 100

    # Identify the top skills per cluster with their average points and percentages
    top_skills_with_avg_and_percent = skill_averages.apply(lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    summary_label = ""
    summaries = []
    data_folder = "sc/ladder-all"

    # Gather data for the report
    clusters = {}
    for cluster, group in df.groupby('Cluster'):
        sorted_group = group.sort_values(by='Level', ascending=False)  # Sort by level descending
        character_count = len(sorted_group)
        cluster_percentage = cluster_counts[cluster]
        equipment_counts = {}
        for row in sorted_group.itertuples():
            for row in sorted_group.itertuples():
                equipment_list = row.Equipment.split(", ")
                for item in equipment_list:
                    if item:
                        worn, title_count = item.split(": ", 1)
                        if " x" in title_count:
                            title, count = title_count.split(" x", 1)
                            count = int(count)
                        else:
                            title = title_count
                            count = 1

                        if worn not in equipment_counts:
                            equipment_counts[worn] = {}
                        if title in equipment_counts[worn]:
                            equipment_counts[worn][title] += count
                        else:
                            equipment_counts[worn][title] = count  # Initialize with real count

        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)

        # Generate HTML report for mercenaries in this cluster
        merc_count = f"<h3>Mercenary Equipment Analysis for Cluster {cluster}</h3>"

        # Mercenary type counts
        merc_count += "<h4>Count of Mercenary Types</h4>"
        for mercenary, count in mercenary_counts.items():
            merc_count += f"<p>{mercenary}: {count}</p>"

        # Mercenary equipment titles
        merc_count += "<h4>Equipment Titles</h4>"
        for mercenary, equipment in mercenary_equipment.items():
            merc_count += f"<p><strong>{mercenary}:</strong></p>"
            for title, count in equipment.items():
                merc_count += f"<p>{title}: {count}</p>"

        # ✅ Fix: Ensure the cluster exists before adding merc_count
        if cluster not in clusters:
            clusters[cluster] = {}

        if 'merc_count' not in clusters[cluster]:
            clusters[cluster]['merc_count'] = merc_count

        # Calculate total counts for each category
        total_counts = {
            worn: sum(titles.values())
            for worn, titles in equipment_counts.items()
        }

        # Calculate the percentages based on total counts
        equipment_percentages = {
            worn: {title: (count / total_counts[worn]) * 100 for title, count in titles.items()}
            for worn, titles in equipment_counts.items()
        }

        # Get top equipment based on count
        top_equipment = {
            worn: sorted(titles.items(), key=lambda item: item[1], reverse=True)[:5]
            for worn, titles in equipment_counts.items()
        }

        # Use equipment_percentages for display
        top_equipment_str_list = []
        for worn, titles in top_equipment.items():
            titles_str = "<br>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;{title} {equipment_percentages[worn][title]:.2f}%" for title, count in titles])
            top_equipment_str_list.append(f"<strong>{worn.capitalize()}</strong>: <br>{titles_str}")

        top_equipment_str = "<br>".join(top_equipment_str_list)

        # Use sorted_equipment_counts for full display
        sorted_equipment_counts = {
            worn: dict(sorted(titles.items(), key=lambda item: item[1], reverse=True))
            for worn, titles in equipment_counts.items()
        }

        equipment_counts_str_list = []
        for worn, titles in sorted_equipment_counts.items():
            titles_str = ", ".join([f"{title} {equipment_percentages[worn][title]:.2f}%" for title in titles])
            equipment_counts_str_list.append(f"<strong>{worn.capitalize()}</strong>: {titles_str}")

        equipment_counts_str = "<br>".join(equipment_counts_str_list)

        # Define a helper function to format numbers
        def format_number(num):
            return int(num) if num % 1 == 0 else round(num, 2)

        # Filter top skills
        top_skills = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]

        # Filter other skills, ignoring those with zero points
        other_skills = skill_averages.loc[cluster].drop(top_skills)
        other_skills = other_skills[other_skills > 0].nlargest(6)
        other_skills_pie = "<br>".join([f"{skill} ({format_number(avg)})" for skill, avg in other_skills.items()])
#        other_skills_str = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(other_skills[skill] * character_count)})" for skill in other_skills.index])
        other_skills_str = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(other_skills[skill] * character_count)})</span>"
            for skill in other_skills.index
        ])

        # Filter remaining skills, ignoring those with zero points
        remaining_skills = skill_averages.loc[cluster].sort_values(ascending=False)
        remaining_skills = remaining_skills[remaining_skills > 0]
#        remaining_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str2 = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(remaining_skills[skill] * character_count)})</span>"
            for skill in remaining_skills.index
        ])
#        remaining_skills_str_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str_with_icons = "\n".join([
            "<div class='skills-group'>" + "\n".join([
                "<div class='skills-row'>" +
                "\n".join([
                    f"<div class='skill-item'>"
                    f"<div class='skillbar-container'>"
                    f"<div class='skill-info'>"
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                    f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})"
                    f"</div>"
                    f"<div class='skill-mini-bar' style='width: {round(skill_percentages.loc[cluster, skill], 2) * 4}px;'></div>"
                    f"</div>"
                    f"</div>"
                    for skill in remaining_skills.index[row:row+2]
                ]) +
                "</div>"  # Close row
                for row in range(i, min(i+10, len(remaining_skills.index)), 2)
            ]) + "</div>"  # Close group
            for i in range(0, len(remaining_skills.index), 10)
        ])

        sorted_summary_label = ""
        summary_labels = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]
        summary = f"{cluster_percentage:.2f}% of {what_class}'s invest heavily in " + ", ".join(summary_labels)
        summaries.append((cluster_percentage, summary))

        clusters[cluster] = {
    #        'label': f"{cluster_percentage:.2f}% of {what_class}'s: <br>" + "<br>".join([f"{skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
#            'label': f"{cluster_percentage:.2f}%  of {what_class}'s Main Skills:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
            'label': f"{cluster_percentage:.2f}% of {what_class}'s Main Skills:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar">
                                <span class="skill-label">{skill} ({int(avg * character_count)})</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
                for skill, avg, percent in top_skills_with_avg_and_percent[cluster]
            ]),
            'character_count': character_count,
            'other_skills': other_skills_str,
            'other_skills_pie': other_skills_pie,
            'characters': [{'name': row.Name, 'level': row.Level, 'skills': row.Skills, 'equipment': row.Equipment, 'mercenary': row.Mercenary, 'mercenary_equipment': row.MercenaryEquipment, 'class': row.Class } for row in sorted_group.itertuples()],
            'top_equipment': top_equipment_str,  # Add top equipment to the data
            'equipment_counts': equipment_counts_str,
            'remaining_skills_with_icons': remaining_skills_str_with_icons,
            'remaining_skills_str2': remaining_skills_str2,  # Add remaining skills string for display without icons
    #        'all_skills_str2': all_skills_str2,
    #        'all_skills_str2_with_icons' : all_skills_str2_with_icons
            'top_5_most_used_skills': top_5_most_used_skills,
            'bottom_5_least_used_skills': bottom_5_least_used_skills,
            'summary_label' : summary_label, 
            'mercenary': mercenary,  # Store mercenary type
            'mercenary_equipment': mercenary_equipment,  # Store mercenary's items
            
        }
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)


    # Ensure the correct percentage values are used
    pie_data = df.groupby('Cluster').agg({
        'Percentage': 'mean',  # Get the mean percentage for each cluster
        'Cluster_Label': 'first'  # Use the first cluster label as representative
    }).reset_index()

    # Include other_skills in customdata
    pie_data['other_skills_pie'] = pie_data['Cluster'].map(lambda cluster: clusters[cluster]['other_skills_pie'])

    # Combine cluster label and percentage for the pie chart labels
    pie_data['Cluster_Label_Percentage'] = pie_data.apply(lambda row: f"{row['Percentage']:.2f}% - Main Skills and avg points: {row['Cluster_Label']}", axis=1)

    import plotly.express as px

    # Get unique clusters
    unique_clusters = sorted(df['Cluster'].unique())  # Sorting ensures consistent ordering

    # Assign colors from a predefined palette
    color_palette = px.colors.qualitative.Safe  # You can change this to Vivid, Bold, etc.
    color_map = {cluster: color_palette[i % len(color_palette)] for i, cluster in enumerate(unique_clusters)}

    # Create a pie chart
    fig_pie = px.pie(
        pie_data,
        values='Percentage',
        names='Cluster_Label_Percentage',
        title=f"{what_class} Skills Distribution",
        hover_data={'Cluster_Label': True, 'other_skills_pie': True},
        color_discrete_map={row['Cluster_Label_Percentage']: color_map[row['Cluster']] for _, row in pie_data.iterrows()}  # ✅ Maps labels to the same colors
    )

    # Update customdata to pass Cluster_Label
    fig_pie.update_traces(customdata=pie_data[['Cluster_Label', 'other_skills_pie']])

    # Customize the hover template for the pie chart
    fig_pie.update_traces(
        textinfo='percent',  # Keep percentages on the pie slices
        textposition='inside',  # Position percentages inside the pie slices
        hovertemplate="<b>%{customdata[0]}</b><br>Other Skills and Average Point Investment:<br>%{customdata[1]}<extra></extra>",
        marker=dict(line=dict(color='black', width=1)),  # Add a slight outline for clarity
        pull=[0.05] * len(pie_data),  # Slightly pull slices apart to increase visibility
        hole=0  # Ensure it's a full pie (not a donut)
    )

    # Position the legend outside the pie chart and adjust the pie chart size
    fig_pie.update_layout(
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",
            y=-0.15,  # Move it closer
            xanchor="center",
            x=0.5,  # Keep it centered
            font=dict(size=10, color='white'),
            bgcolor='rgba(0,0,0,0)',
#                font=dict(color='white'),  # ✅ Transparent background
        ),
        paper_bgcolor='rgba(0,0,0,0)', # ✅ Transparent background
        margin=dict(l=10, r=10, t=50, b=20),  # Reduce bottom margin to make more space
        width=900,  # Set the width of the entire chart
        height=600,  # Set the height of the entire chart
        font=dict(color='white'),  # ✅ Makes all text white
        title=dict(font=dict(color='white')),  # ✅ Ensures title is also white
#            legend=dict(font=dict(color='white'))  # ✅ Ensures legend text is white
    )

    # Increase the pie size explicitly
    fig_pie.update_traces(domain=dict(x=[0, 1], y=[0.1, 1]))  # Expands pie upward

    # Save the pie chart as a PNG file
    fig_pie.write_image(f"pod-stats/charts/{what_class}-clusters_distribution_pie.png")

    # Create a DataFrame for visualization
    plot_data = pd.DataFrame({
        'PCA1': reduced_data[:, 0],
        'PCA2': reduced_data[:, 1],
        'Cluster': df['Cluster'],
        'Cluster_Label': df['Cluster_Label'],
        'Percentage': df['Percentage']
    })

    # Create an interactive scatter plot
    fig_scatter = px.scatter(
        plot_data,
        x='PCA1',
        y='PCA2',
        color='Cluster',  # Assign color based on the cluster
        title=f"{what_class} Skill Clusters (Ladder Top 200 {what_class}'s Highlighted)<br>This highlights how similar (or not) a character is to the rest<br>The tighter the grouping, the more they are alike",
        hover_data={'Cluster_Label': True, 'Percentage': ':.2f%', 'Cluster': True},
        color_discrete_map=color_map  # Use the same colors as the pie chart
    )

    # Customize the legend labels
    for trace in fig_scatter.data:
        if trace.name.isnumeric():  # Ensure that the trace name is numeric
            trace.update(name=legend_labels[int(trace.name)])

    # Customize hover template to include top skills and percentage
    fig_scatter.update_traces(
        hovertemplate="<b>Cluster skills and average point investment:</b><br> %{customdata[0]}<br>" +
                    "This cluster (%{customdata[2]}) makes up %{customdata[1]:.2f}% of the total<extra></extra>"
    )

    # Hide the axis titles and tick labels
    fig_scatter.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        xaxis_showticklabels=False,
        yaxis_showticklabels=False
    )

    # Save the scatter plot as a PNG file
    fig_scatter.write_image(f"pod-stats/charts/{what_class}-clusters_with_avg_points.png")

    print("Pie chart and scatter plot saved as PNG files.")


    # Sort clusters by percentage in descending order
    sorted_clusters = dict(sorted(clusters.items(), key=lambda item: item[1]['character_count'], reverse=True))

    # Split the entries into a list
    entries = summary_label.strip().split("<br>\n")
    # Remove any empty strings from the list (if any)
    entries = [entry for entry in entries if entry.strip()]
    # Sort the entries in descending order based on the percentage value
    sorted_entries = sorted(entries, key=lambda x: float(x.split('%')[0]), reverse=False)
    # Join the sorted entries back into a single string
    sorted_summaries = sorted(summaries, key=lambda x: x[0], reverse=True)
    summary_label = "<br>".join(summary for _, summary in sorted_summaries)
    #print(summary_label)

    # Ensure the cluster exists before adding merc_count
    if cluster not in clusters:
        clusters[cluster] = {}

    clusters[cluster]['merc_count'] = merc_count

    print(f"✅ Added merc data for cluster {cluster}:")
    print(merc_count)

    dt = datetime.now()
    # format it to a string
    timeStamp = dt.strftime('%Y-%m-%d %H:%M')
    
    # Render the HTML report
    template = Template(html_template)
    html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, timeStamp=timeStamp)  # Pass sorted clusters to the template

    # Save the report to a file
    output_file = f"pod-stats/{what_class}.html"
    with open(output_file, "w") as file:
        file.write(html_content)

    print(f"Cluster analysis report saved to {output_file}")

#GetDashers()



###############################################################
#
# Get non Amazon bow users
#
# Item colors good to go
def GetNonZon():
    icons_folder = "icons"
    what_class = "Notazons"
    search_tags = {"Bolts", "Arrows"}  # Use a set for faster lookups
    howmany_clusters = 6
    howmany_skills = 4

    # Load the consolidated JSON file
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)

    # Filter characters based on equipped items
    filtered_characters = []
    for char_data in all_characters:
            # Exclude characters of the class "Amazon"
        if char_data.get("Class") == "Amazon":
            continue  # Skip this character

        for item in char_data.get("Equipped", []):
            if item.get("Tag") in search_tags:
                filtered_characters.append(char_data)
                break  # No need to check further items

    def map_readable_names(mercenary_type, worn_category=""):
        mercenary_mapping = {
            "Desert Mercenary": "Act 2 Desert Mercenary",
            "Rogue Scout": "Act 1 Rogue Scout",
            "Eastern Sorceror": "Act 3 Eastern Sorceror",
            "Barbarian": "Act 5 Barbarian"
        }
        worn_mapping = {
            "body": "Armor",
            "helmet": "Helmet",
            "weapon1": "Weapon",
            "weapon2": "Offhand"
        }
        readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
        readable_worn = worn_mapping.get(worn_category, worn_category)
        return readable_mercenary, readable_worn

    def load_data(filtered_characters):
        all_data = []
        quality_colors = {
            "q_runeword": "#edcd74",
            "q_unique": "#edcd74",
            "q_set": "#45a823",
            "q_magic": "#7074c9",
            "q_rare": "yellow",
            "q_crafted": "orange"
        }

        for char_data in filtered_characters:
            if "SkillTabs" in char_data and "Equipped" in char_data:
                skill_data = {
                    "Name": char_data.get("Name", "Unknown"),
                    "Class": char_data.get("Class", "Unknown"),
                    "Level": char_data.get("Stats", {}).get("Level", "Unknown")
                }

                # Extract and sort skills
            skills = []
            for tab in char_data.get('SkillTabs', []):
                for skill in tab.get('Skills', []):
                    skill_name = skill['Name']
                    skill_level = skill['Level']
                    skill_data[skill_name] = skill_level  # ✅ Creates a separate column for each skill
                    skills.append((skill_name, skill_level))
                skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                skill_data["Skills"] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])

                # Process equipment
                equipment_titles = defaultdict(Counter)
                for item in char_data["Equipped"]:
                    worn_category = item.get("Worn", "Unknown")
                    title = item.get("Title", "Unknown")
                    quality_code = item.get("QualityCode", "default")
                    tag = item.get("Tag", "")

                    # Apply proper naming and colors
                    worn_category = {
                        "ring1": "Ring", "ring2": "Ring",
                        "sweapon1": "Left hand", "weapon1": "Left hand",
                        "sweapon2": "Offhand", "weapon2": "Offhand",
                        "body": "Armor", "gloves": "Gloves",
                        "belt": "Belt", "helmet": "Helmet",
                        "boots": "Boots", "amulet": "Amulet"
                    }.get(worn_category, worn_category)

                    # Set colored title
                    if quality_code in quality_colors:
                        color = quality_colors[quality_code]
                        if quality_code in ["q_magic", "q_rare", "q_crafted"]:
                            colored_title = f"<span style='color: {color};'>{quality_code.split('_')[1].capitalize()} {tag}</span>"
                        else:
                            colored_title = f"<span style='color: {color};'>{title}</span>"
                    else:
                        colored_title = title  # Default title if no color mapping

                    equipment_titles[worn_category][colored_title] += 1

                # Convert equipment data to a readable string
                skill_data["Equipment"] = ", ".join([
                    f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                    for worn, titles in equipment_titles.items()
                    for title, count in titles.items()
                ])

                # Process mercenary info
                mercenary_type = char_data.get("MercenaryType", "No mercenary")
                readable_mercenary, _ = map_readable_names(mercenary_type)
                mercenary_equipment = ", ".join(
                    [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                ) if char_data.get("MercenaryEquipped") else "No equipment"

                skill_data["Mercenary"] = readable_mercenary
                skill_data["MercenaryEquipment"] = mercenary_equipment

                all_data.append(skill_data)

        return pd.DataFrame(all_data).fillna(0)  # Fill missing skills with 0

    # Load the data
    df = load_data(filtered_characters)

    # Define skill columns (exclude non-skill columns)
#    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment']]
    # Ensure skill_columns only includes numeric skill values
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment']]

    # Perform PCA
    pca = PCA(n_components=2)
    reduced_data = pca.fit_transform(df[skill_columns])

#    print(df.dtypes)  # Check which columns are non-numeric
#    print(df.head())  # See if 'Mercenary' appears in the dataset

    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=howmany_clusters, random_state=42)
    df['Cluster'] = kmeans.fit_predict(df[skill_columns])

    # Calculate the average points invested in skills per cluster
    df['Total_Points'] = df[skill_columns].sum(axis=1)
    cluster_averages = df.groupby('Cluster')['Total_Points'].mean().reset_index()
    cluster_averages.columns = ['Cluster', 'Avg_Points']

    # Merge the averages back into the main DataFrame
    df = pd.merge(df, cluster_averages, on='Cluster')

    # Get skill averages per cluster
    skill_averages = df.groupby('Cluster')[skill_columns].mean()

    # Identify the top skills per cluster with their average points
    top_skills_with_avg = skill_averages.apply(lambda x: [(skill, round(x[skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    # Calculate the correct percentages for each cluster
    cluster_counts = df['Cluster'].value_counts(normalize=True) * 100
    df['Percentage'] = df['Cluster'].map(cluster_counts)

    # Map clusters to meaningful names (top skills with average points)
    cluster_labels = {i: ", ".join([f"{skill} ({avg})" for skill, avg in skills]) for i, skills in enumerate(top_skills_with_avg)}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Updated HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ what_class }} Analysis Report</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

    </head>
    <body class="not-main">

        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>

        <h1>{{ what_class }} Softcore Skill Distribution </h1>
        <div class="summary-container">
        <br>
        <h3>The Notazon is not a Zon, but has bolts or arrows equipped</h3>

        {% for clusters, data in clusters.items() %}
        <!--<h2>{{ data['label'] }}</h2>
        <p class="indented-skills"><strong>Other Skills:<br></strong> {{ data['other_skills'] }}</p> -->
        <div class="class-intro">
        <div id="skills" class="skills-container">
            <div class="column">
                <ul id="most-popular-skills">
                    <h2>{{ data['label'] }}</h2>
                </ul>
            </div>
<!--            <div class="column">
                <ul id="other-skills">
                    <h2>Other common skills in this group:</h2> {{ data['other_skills'] }}
                </ul>
            </div> -->
        </div>

        
    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>All Skills</strong></button>
                <div class="content">
                    <div>{{ data['remaining_skills_with_icons'] }}</div>
                </div>



                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>Most Common Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['top_equipment'] }}</div>
                </div>
<!--        
            <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>ALL Equipment:</strong></button>
            <div class="content">
                <div>{{ data['equipment_counts'] }}</div>
            </div>
-->
             <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>{{ data['character_count'] }} Characters in this cluster:</strong>
        </button>
        <div class="content">
{% for character in data['characters'] %}
<!--
<div class="character-container {% if loop.index is even %}char1{% else %}char2{% endif %}">
-->
<div class="character-container char2">
    <div class="character-info">
        <div class="character-link"><strong>Name: <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}
            </a></strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="hover-trigger" data-character-name="{{ character['name'] }}">
            <!-- Armory Quickview -->
        </div>
    </div>

    <div class="character">
        <div class="popup hidden"></div> <!-- No iframe inside initially -->
    </div>

    <p><strong>Skills:<br></strong> {{ character['skills'] }}</p>
    <p><strong>Equipment:<br></strong> {{ character['equipment'] }}</p>
    <p><strong>Mercenary:<br></strong> {{ character['mercenary'] }} - {{ character['mercenary_equipment'] }}</p>

    <div class="character-section" data-character-name="{{ character['name'] }}"></div>
</div>
<hr color="#141414">
<br>
{% endfor %}
            <br>
            </div>
            </div>
        <!--    <hr width="90%"> -->
            <br>
                {% endfor %}
            </ul>
            <br>
            <hr>
            <br>
        <p class="indented-skills">Popular builds include:<br>{{ summary_label }} </p>
            <br>
            </div>
            <br><br>
                    <!-- Embed the Plotly pie chart -->
        <div>
            <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
        </div>

        <!-- Embed the Plotly scatter plot -->
        <div>
            <img src="charts/{{ what_class }}-clusters_with_avg_points.png" alt="{{ what_class }} Skill Clusters Scatter Plot">
        </div>
        <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>
            <div class="footer">
            <p>PoD data current as of {{ timeStamp }}</p>
            </div>
        



<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}


//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}


document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});

document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});

document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>





    </body>
    </html>
    """

        
    def analyze_mercenaries(characters):
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        for char_data in characters:
            if not isinstance(char_data, dict):
                print(f"Skipping unexpected data format: {char_data}")
                continue  # Skip invalid entries

            mercenary = char_data.get("MercenaryType")
            if mercenary:
                readable_mercenary, _ = map_readable_names(mercenary, "")
                mercenary_counts[readable_mercenary] += 1

                for item in char_data.get("MercenaryEquipped", []):
                    worn_category = item.get("Worn", "Unknown")
                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                    title = item.get("Title", "Unknown")
                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1

        return mercenary, mercenary_counts, mercenary_equipment



    # Assuming df is your DataFrame and skill_columns contains the column names for the skills

    # Calculate the total usage of each skill across all clusters
    total_skill_usage = df[skill_columns].sum()

    # Sort skills by total usage in descending order
    most_used_skills = total_skill_usage.sort_values(ascending=False)

    # Sort skills by total usage in ascending order
    least_used_skills = total_skill_usage.sort_values(ascending=True)

    # Extract the top 5 most used skills
    top_5_most_used_skills = most_used_skills.head(5)

    # Extract the bottom 5 least used skills
    bottom_5_least_used_skills = least_used_skills.head(5)


    # Calculate the percentage of characters that have invested in each skill within the cluster
    skill_percentages = df[skill_columns].astype(bool).groupby(df['Cluster']).mean() * 100

    # Identify the top skills per cluster with their average points and percentages
    top_skills_with_avg_and_percent = skill_averages.apply(lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    summary_label = ""
    summaries = []
#    data_folder = "sc/ladder-all"

    # Gather data for the report
    clusters = {}
    for cluster, group in df.groupby('Cluster'):
        sorted_group = group.sort_values(by='Level', ascending=False)  # Sort by level descending
        character_count = len(sorted_group)
        cluster_percentage = cluster_counts[cluster]
        equipment_counts = {}
        for row in sorted_group.itertuples():
            equipment_list = row.Equipment.split(", ")
            for item in equipment_list:
                if item:
                    worn, title_count = item.split(": ", 1)
                    if " x" in title_count:
                        title, count = title_count.split(" x", 1)
                        count = int(count)
                    else:
                        title = title_count
                        count = 1

                    if worn not in equipment_counts:
                        equipment_counts[worn] = {}
                    if title in equipment_counts[worn]:
                        equipment_counts[worn][title] += count
                    else:
                        equipment_counts[worn][title] = count  # Initialize with real count


#            print("🔹 Original Equipment Counts:")
#            pp.pprint(equipment_counts)

        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)

        # Generate HTML report for mercenaries in this cluster
        merc_count = f"<h3>Mercenary Equipment Analysis for Cluster {cluster}</h3>"

        # Mercenary type counts
        merc_count += "<h4>Count of Mercenary Types</h4>"
        for mercenary, count in mercenary_counts.items():
            merc_count += f"<p>{mercenary}: {count}</p>"

        # Mercenary equipment titles
        merc_count += "<h4>Equipment Titles</h4>"
        for mercenary, equipment in mercenary_equipment.items():
            merc_count += f"<p><strong>{mercenary}:</strong></p>"
            for title, count in equipment.items():
                merc_count += f"<p>{title}: {count}</p>"

        # ✅ Fix: Ensure the cluster exists before adding merc_count
        if cluster not in clusters:
            clusters[cluster] = {}

        if 'merc_count' not in clusters[cluster]:
            clusters[cluster]['merc_count'] = merc_count

        # Calculate total counts for each category
        total_counts = {
            worn: sum(titles.values())
            for worn, titles in equipment_counts.items()
        }

        # Calculate the percentages based on total counts
        equipment_percentages = {
            worn: {title: (count / total_counts[worn]) * 100 for title, count in titles.items()}
            for worn, titles in equipment_counts.items()
        }

        # Get top equipment based on count
        top_equipment = {
            worn: sorted(titles.items(), key=lambda item: item[1], reverse=True)[:5]
            for worn, titles in equipment_counts.items()
        }

        # Use equipment_percentages for display
        top_equipment_str_list = []
        for worn, titles in top_equipment.items():
            titles_str = "<br>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;{title} {equipment_percentages[worn][title]:.2f}% ({count})" for title, count in titles])
            top_equipment_str_list.append(f"<strong>{worn.capitalize()}</strong>: <br>{titles_str}")

        top_equipment_str = "<br>".join(top_equipment_str_list)

        # Use sorted_equipment_counts for full display
        sorted_equipment_counts = {
            worn: dict(sorted(titles.items(), key=lambda item: item[1], reverse=True))
            for worn, titles in equipment_counts.items()
        }

        equipment_counts_str_list = []
        for worn, titles in sorted_equipment_counts.items():
            titles_str = ", ".join([f"{title} {equipment_percentages[worn][title]:.2f}%" for title in titles])
            equipment_counts_str_list.append(f"<strong>{worn.capitalize()}</strong>: {titles_str}")

        equipment_counts_str = "<br>".join(equipment_counts_str_list)


        # Define a helper function to format numbers
        def format_number(num):
            return int(num) if num % 1 == 0 else round(num, 2)

        # Filter top skills
        top_skills = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]

        # Filter other skills, ignoring those with zero points
        other_skills = skill_averages.loc[cluster].drop(top_skills)
        other_skills = other_skills[other_skills > 0].nlargest(6)
        other_skills_pie = "<br>".join([f"{skill} ({format_number(avg)})" for skill, avg in other_skills.items()])
#        other_skills_str = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(other_skills[skill] * character_count)})" for skill in other_skills.index])
        other_skills_str = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(other_skills[skill] * character_count)})</span>"
            for skill in other_skills.index
        ])

        # Filter remaining skills, ignoring those with zero points
        remaining_skills = skill_averages.loc[cluster].sort_values(ascending=False)
        remaining_skills = remaining_skills[remaining_skills > 0]
#        remaining_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str2 = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(remaining_skills[skill] * character_count)})</span>"
            for skill in remaining_skills.index
        ])
#        remaining_skills_str_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str_with_icons = "\n".join([
            "<div class='skills-group'>" + "\n".join([
                "<div class='skills-row'>" +
                "\n".join([
                    f"<div class='skill-item'>"
                    f"<div class='skillbar-container'>"
                    f"<div class='skill-info'>"
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                    f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})"
                    f"</div>"
                    f"<div class='skill-mini-bar' style='width: {round(skill_percentages.loc[cluster, skill], 2) * 4}px;'></div>"
                    f"</div>"
                    f"</div>"
                    for skill in remaining_skills.index[row:row+2]
                ]) +
                "</div>"  # Close row
                for row in range(i, min(i+10, len(remaining_skills.index)), 2)
            ]) + "</div>"  # Close group
            for i in range(0, len(remaining_skills.index), 10)
        ])
    #    all_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
    #    all_skills_str2_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
        sorted_summary_label = ""
        summary_labels = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]
        summary = f"{cluster_percentage:.2f}% of {what_class}'s invest heavily in " + ", ".join(summary_labels)
        summaries.append((cluster_percentage, summary))

        clusters[cluster] = {
    #        'label': f"{cluster_percentage:.2f}% of {what_class}'s: <br>" + "<br>".join([f"{skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
#            'label': f"{cluster_percentage:.2f}%  of {what_class}'s Main Skills:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
            'label': f"{cluster_percentage:.2f}% of {what_class}'s Main Skills:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar">
                                <span class="skill-label">{skill} ({int(avg * character_count)})</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
                for skill, avg, percent in top_skills_with_avg_and_percent[cluster]
            ]),
           'character_count': character_count,
            'other_skills': other_skills_str,
            'other_skills_pie': other_skills_pie,
            'characters': [{'name': row.Name, 'level': row.Level, 'skills': row.Skills, 'equipment': row.Equipment, 'mercenary': row.Mercenary, 'mercenary_equipment': row.MercenaryEquipment, 'class': row.Class } for row in sorted_group.itertuples()],
            'top_equipment': top_equipment_str,  # Add top equipment to the data
            'equipment_counts': equipment_counts_str,
            'remaining_skills_with_icons': remaining_skills_str_with_icons,
            'remaining_skills_str2': remaining_skills_str2,  # Add remaining skills string for display without icons
    #        'all_skills_str2': all_skills_str2,
    #        'all_skills_str2_with_icons' : all_skills_str2_with_icons
            'top_5_most_used_skills': top_5_most_used_skills,
            'bottom_5_least_used_skills': bottom_5_least_used_skills,
            'summary_label' : summary_label, 
            'merc_count': merc_count,
#            'mercenary': row.Mercenary,  # Store mercenary type
#            'mercenary_equipment': row.MercenaryEquipment  # Store mercenary's items
            'mercenary': mercenary,  # Store mercenary type
            'mercenary_equipment': mercenary_equipment,  # Store mercenary's items
            
        }
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)
        


    # Ensure the correct percentage values are used
    pie_data = df.groupby('Cluster').agg({
        'Percentage': 'mean',  # Get the mean percentage for each cluster
        'Cluster_Label': 'first'  # Use the first cluster label as representative
    }).reset_index()

    # Include other_skills in customdata
    pie_data['other_skills_pie'] = pie_data['Cluster'].map(lambda cluster: clusters[cluster]['other_skills_pie'])

    # Combine cluster label and percentage for the pie chart labels
    pie_data['Cluster_Label_Percentage'] = pie_data.apply(lambda row: f"{row['Percentage']:.2f}% - Main Skills and avg points: {row['Cluster_Label']}", axis=1)

    import plotly.express as px

    # Get unique clusters
    unique_clusters = sorted(df['Cluster'].unique())  # Sorting ensures consistent ordering

    # Assign colors from a predefined palette
    color_palette = px.colors.qualitative.Safe  # You can change this to Vivid, Bold, etc.
    color_map = {cluster: color_palette[i % len(color_palette)] for i, cluster in enumerate(unique_clusters)}

    # Create a pie chart
    fig_pie = px.pie(
        pie_data,
        values='Percentage',
        names='Cluster_Label_Percentage',
        title=f"{what_class} Skills Distribution",
        hover_data={'Cluster_Label': True, 'other_skills_pie': True},
        color_discrete_map={row['Cluster_Label_Percentage']: color_map[row['Cluster']] for _, row in pie_data.iterrows()}  # ✅ Maps labels to the same colors
    )

    # Update customdata to pass Cluster_Label
    fig_pie.update_traces(customdata=pie_data[['Cluster_Label', 'other_skills_pie']])

    # Customize the hover template for the pie chart
    fig_pie.update_traces(
        textinfo='percent',  # Keep percentages on the pie slices
        textposition='inside',  # Position percentages inside the pie slices
        hovertemplate="<b>%{customdata[0]}</b><br>Other Skills and Average Point Investment:<br>%{customdata[1]}<extra></extra>",
        marker=dict(line=dict(color='black', width=1)),  # Add a slight outline for clarity
        pull=[0.05] * len(pie_data),  # Slightly pull slices apart to increase visibility
        hole=0  # Ensure it's a full pie (not a donut)
    )

    # Position the legend outside the pie chart and adjust the pie chart size
    fig_pie.update_layout(
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",
            y=-0.15,  # Move it closer
            xanchor="center",
            x=0.5,  # Keep it centered
            font=dict(size=10, color='white'),
            bgcolor='rgba(0,0,0,0)',
#                font=dict(color='white'),  # ✅ Transparent background
        ),
        paper_bgcolor='rgba(0,0,0,0)', # ✅ Transparent background
        margin=dict(l=10, r=10, t=50, b=20),  # Reduce bottom margin to make more space
        width=900,  # Set the width of the entire chart
        height=600,  # Set the height of the entire chart
        font=dict(color='white'),  # ✅ Makes all text white
        title=dict(font=dict(color='white')),  # ✅ Ensures title is also white
#            legend=dict(font=dict(color='white'))  # ✅ Ensures legend text is white
    )

    # Increase the pie size explicitly
    fig_pie.update_traces(domain=dict(x=[0, 1], y=[0.1, 1]))  # Expands pie upward

    # Save the pie chart as a PNG file
    fig_pie.write_image(f"pod-stats/charts/{what_class}-clusters_distribution_pie.png")

    # Create a DataFrame for visualization
    plot_data = pd.DataFrame({
        'PCA1': reduced_data[:, 0],
        'PCA2': reduced_data[:, 1],
        'Cluster': df['Cluster'],
        'Cluster_Label': df['Cluster_Label'],
        'Percentage': df['Percentage']
    })

    # Create an interactive scatter plot
    fig_scatter = px.scatter(
        plot_data,
        x='PCA1',
        y='PCA2',
        color='Cluster',  # Assign color based on the cluster
        title=f"{what_class} Skill Clusters (Ladder Top 200 {what_class}'s Highlighted)<br>This highlights how similar (or not) a character is to the rest<br>The tighter the grouping, the more they are alike",
        hover_data={'Cluster_Label': True, 'Percentage': ':.2f%', 'Cluster': True},
        color_discrete_map=color_map  # Use the same colors as the pie chart
    )

    # Customize the legend labels
    for trace in fig_scatter.data:
        if trace.name.isnumeric():  # Ensure that the trace name is numeric
            trace.update(name=legend_labels[int(trace.name)])

    # Customize hover template to include top skills and percentage
    fig_scatter.update_traces(
        hovertemplate="<b>Cluster skills and average point investment:</b><br> %{customdata[0]}<br>" +
                    "This cluster (%{customdata[2]}) makes up %{customdata[1]:.2f}% of the total<extra></extra>"
    )

    # Hide the axis titles and tick labels
    fig_scatter.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        xaxis_showticklabels=False,
        yaxis_showticklabels=False
    )

    # Save the scatter plot as a PNG file
    fig_scatter.write_image(f"pod-stats/charts/{what_class}-clusters_with_avg_points.png")

    print("Pie chart and scatter plot saved as PNG files.")

    # Sort clusters by percentage in descending order
    sorted_clusters = dict(sorted(clusters.items(), key=lambda item: item[1]['character_count'], reverse=True))

    # Split the entries into a list
    entries = summary_label.strip().split("<br>\n")
    # Remove any empty strings from the list (if any)
    entries = [entry for entry in entries if entry.strip()]
    # Sort the entries in descending order based on the percentage value
    sorted_entries = sorted(entries, key=lambda x: float(x.split('%')[0]), reverse=False)
    # Join the sorted entries back into a single string
    sorted_summaries = sorted(summaries, key=lambda x: x[0], reverse=True)
    summary_label = "<br>".join(summary for _, summary in sorted_summaries)
    #print(summary_label)

#    for cluster, data in clusters.items():
#        print(f"Cluster {cluster}:")
#        print(data.get("merc_count", "No merc data found"))

    # Ensure the cluster exists before adding merc_count
    if cluster not in clusters:
        clusters[cluster] = {}

    clusters[cluster]['merc_count'] = merc_count

#    print(f"✅ Added merc data for cluster {cluster}:")
#    print(merc_count)

    dt = datetime.now()
    # format it to a string
    timeStamp = dt.strftime('%Y-%m-%d %H:%M')

    # Render the HTML report
    template = Template(html_template)
    html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, timeStamp=timeStamp)  # Pass sorted clusters to the template

    # Save the report to a file
    output_file = f"pod-stats/{what_class}.html"
    with open(output_file, "w") as file:
        file.write(html_content)

    print(f"Cluster analysis report saved to {output_file}")

#GetNonZon()

###############################################################
#
# Get Uniques Arrows and Bolts
#
import requests
import os
import time
# Get non zon
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import plotly.express as px
import json
import os
from jinja2 import Template
## No Item Colors : (
def GetUniqueProjectiles():
    icons_folder = "icons"
    what_class = "Unique_Bolts_and_Arrows"
    search_tags = ["Dragonbreath", "Swiftheart", "Moonfire", "Frostbite", "Hailstorm"]
    search_tags2 = ["Unique"]
    howmany_clusters = 6
    howmany_skills = 4

    # Load the consolidated JSON file
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)

    # Filter characters based on equipped items
    filtered_characters = []
    for char_data in all_characters:
            # Exclude characters of the class "Amazon"

        for item in char_data.get("Equipped", []):
            if item["Title"] in search_tags and item["QualityCode"] == "q_unique":
                filtered_characters.append(char_data)
                break  # No need to check further items

    def map_readable_names(mercenary_type, worn_category=""):
        mercenary_mapping = {
            "Desert Mercenary": "Act 2 Desert Mercenary",
            "Rogue Scout": "Act 1 Rogue Scout",
            "Eastern Sorceror": "Act 3 Eastern Sorceror",
            "Barbarian": "Act 5 Barbarian"
        }
        worn_mapping = {
            "body": "Armor",
            "helmet": "Helmet",
            "weapon1": "Weapon",
            "weapon2": "Offhand"
        }
        readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
        readable_worn = worn_mapping.get(worn_category, worn_category)
        return readable_mercenary, readable_worn

    def load_data(filtered_characters):
        all_data = []
        quality_colors = {
            "q_runeword": "#edcd74",
            "q_unique": "#edcd74",
            "q_set": "#45a823",
            "q_magic": "#7074c9",
            "q_rare": "yellow",
            "q_crafted": "orange"
        }

        for char_data in filtered_characters:
                    if 'SkillTabs' in char_data and 'Equipped' in char_data:
#                        print(f"✅ Valid data in: {file_path}")  # Debug: Confirm valid file
                        quality_colors = {
                            "q_runeword": "#edcd74",
                            "q_unique": "#edcd74",
                            "q_set": "#45a823",
                            "q_magic": "#7074c9",#7074c9
#                            "q_magic": "lightblue",#7074c9
                            "q_rare": "yellow",
                            "q_crafted": "orange"
                        }


                        skill_data = {}
                        skill_data['Name'] = char_data.get('Name', 'Unknown')
                        skill_data['Class'] = char_data.get('Class', 'Unknown')
                        skill_data['Level'] = char_data.get('Stats', {}).get('Level', 'Unknown')

                        # Flatten skill data and sort in descending order by points
                        skills = []
                        for tab in char_data['SkillTabs']:
                            for skill in tab['Skills']:
                                skill_name = skill['Name']
                                skill_level = skill['Level']
                                skill_data[skill_name] = skill_level
                                skills.append((skill_name, skill_level))
                        skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                        skill_data['Skills'] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])

                        # Initialize equipment dictionaries
                        equipment_titles = {}
                        clean_equipment_titles = {}

                        # Flatten equipment data
                        for item in char_data['Equipped']:
                            worn_category = item.get('Worn', 'Unknown')
                            title = item.get('Title', 'Unknown')
                            tag = item.get('Tag', 'Unknown')
                            quality = item.get('Quality', 'Unknown')
                            title_tag = f"{title} {tag}"  # Combine Title and Tag

                            # Apply font color based on quality
                            quality_code = item.get('QualityCode', 'default')
                            color = quality_colors.get(quality_code, "white")  # Default white
                            colored_title = f"<span style='color: {color};'>{title}</span>"

                            if worn_category in ['ring1', 'ring2']:
                                worn_category = 'ring'
                            elif worn_category in ['sweapon1', 'weapon1']:
                                worn_category = 'Left hand'
                            elif worn_category in ['sweapon2', 'weapon2']:
                                worn_category = 'Offhand'
                            elif worn_category in ['body']:
                                worn_category = 'Armor'
                            elif worn_category in ['gloves']:
                                worn_category = 'Gloves'
                            elif worn_category in ['belt']:
                                worn_category = 'Belt'
                            elif worn_category in ['helmet']:
                                worn_category = 'Helmet'
                            elif worn_category in ['boots']:
                                worn_category = 'Boots'
                            elif worn_category in ['amulet']:
                                worn_category = 'Amulet'
                            elif worn_category in ['ring']:
                                worn_category = 'Ring'
                            if worn_category not in equipment_titles:
                                equipment_titles[worn_category] = {}
                            # Ensure category exists
                            if worn_category not in equipment_titles:
                                equipment_titles[worn_category] = {}
                            if worn_category not in clean_equipment_titles:
                                clean_equipment_titles[worn_category] = {}

                            # Store colored titles for display
                            if colored_title in equipment_titles[worn_category]:  # ✅ Only use `colored_title`
                                equipment_titles[worn_category][colored_title] += 1
                            else:
                                equipment_titles[worn_category][colored_title] = 1  # ✅ Start from 1, no x0

                            # Store uncolored titles separately for clustering
                            if title_tag not in clean_equipment_titles[worn_category]:
                                clean_equipment_titles[worn_category][title_tag] = 0
                            clean_equipment_titles[worn_category][title_tag] += 1

                        # Format the Equipment string for display
                        skill_data['Equipment'] = ", ".join([
                            f"{worn}: {title_tag} x{count}" if count > 1 else f"{worn}: {title_tag}"
                            for worn, titles in clean_equipment_titles.items() 
                            for title_tag, count in titles.items()
                        ])

                        # Add item presence information
                        for tag in search_tags:
                            skill_data[tag] = 1 if any(item.get('Tag') == tag and item.get('Quality') == 'Unique' for item in char_data['Equipped']) else 0

                        # Store mercenary data
                        mercenary_data = char_data.get("MercenaryType", "No mercenary")
                        readable_mercenary, _ = map_readable_names(mercenary_data)
                        mercenary_equipment = ", ".join(
                            [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                        ) if char_data.get("MercenaryEquipped") else "No equipment"

                        skill_data['Mercenary'] = readable_mercenary
                        skill_data['MercenaryEquipment'] = mercenary_equipment
                        all_data.append(skill_data)

        return pd.DataFrame(all_data).fillna(0)  # Fill missing skills with 0

    # Example usage:
    df = load_data(filtered_characters)

    # Define skill columns (exclude non-skill columns)
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment'] + search_tags]
#    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment'] + search_tags]

    # Filter for unique arrows and bolts only
    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [
        part.split(' x')[0] for part in eq.split(', ') 
        if any(tag in part for tag in search_tags)  # Match against known unique items
    ])
#    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [part.split(' x')[0] for part in eq.split(', ') if 'Bolts' in part or 'Arrows' in part])
#    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [part.split(' x')[0] for part in eq.split(', ') if 'Bolts' in part or 'Arrows' in part])
#    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [part.split(' x')[0] for part in eq.split(', ') if ('Bolts' in part or 'Arrows' in part) and 'Unique' in part])


    # Explode the DataFrame to create one row per item
    df = df.explode('Title_Tag')

    # Remove worn category from Title_Tag
    df['Title_Tag'] = df['Title_Tag'].apply(lambda x: x.split(': ')[1] if ': ' in x else x)

    # Create clusters based on item presence (Title + Tag)
    df['Cluster'] = df['Title_Tag']

    # Calculate the average points invested in skills per cluster
    df['Total_Points'] = df[skill_columns].sum(axis=1)
    cluster_averages = df.groupby('Cluster')['Total_Points'].mean().reset_index()
    cluster_averages.columns = ['Cluster', 'Avg_Points']

    # Merge the averages back into the main DataFrame
    df = pd.merge(df, cluster_averages, on='Cluster')

    # Get skill averages per cluster
    skill_averages = df.groupby('Cluster')[skill_columns].mean()

    # Identify the top skills per cluster with their average points
    top_skills_with_avg = skill_averages.apply(lambda x: [(skill, round(x[skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    # Calculate the correct percentages for each cluster
    cluster_counts = df['Cluster'].value_counts(normalize=True) * 100
    df['Percentage'] = df['Cluster'].map(cluster_counts)

    # Map clusters to meaningful names (top skills with average points)
#    cluster_labels = {i: ", ".join([f"{skill} ({avg})" for skill, avg in skills]) for i, skills in enumerate(top_skills_with_avg)}
#    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)
    cluster_labels = {cluster: f"{cluster}" for cluster in df['Cluster'].unique()}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Updated HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ what_class }} Analysis Report</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

    </head>
    <body class="not-main">

        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>

        <h1>Unique Arrows and Bolts </h1>
        <div class="summary-container">
        <br>
        <h3>Let's see which Unique projectiles are being used</h3>

        {% for clusters, data in clusters.items() %}
        <!--<h2>{{ data['label'] }}</h2>
        <p class="indented-skills"><strong>Other Skills:<br></strong> {{ data['other_skills'] }}</p> -->
        <div class="class-intro">
        <div id="skills" class="skills-container">
            <div class="column">
                <ul id="most-popular-skills">
                    <h2>{{ data['label'] }}</h2>
                </ul>
            </div>
<!--            <div class="column">
                <ul id="other-skills">
                    <h2>Other common skills in this group:</h2> {{ data['other_skills'] }}
                </ul>
            </div> -->
        </div>

        
    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>All Skills</strong></button>
                <div class="content">
                    <div>{{ data['remaining_skills_with_icons'] }}</div>
                </div>



                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>Most Common Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['top_equipment'] }}</div>
                </div>
<!--        
            <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>ALL Equipment:</strong></button>
            <div class="content">
                <div>{{ data['equipment_counts'] }}</div>
            </div>
-->
             <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>{{ data['character_count'] }} Characters in this cluster:</strong>
        </button>
        <div class="content">
{% for character in data['characters'] %}
<!--
<div class="character-container {% if loop.index is even %}char1{% else %}char2{% endif %}">
-->
<div class="character-container char2">
    <div class="character-info">
        <div class="character-link"><strong>Name: <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}
            </a></strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="hover-trigger" data-character-name="{{ character['name'] }}">
            <!-- Armory Quickview -->
        </div>
    </div>

    <div class="character">
        <div class="popup hidden"></div> <!-- No iframe inside initially -->
    </div>

    <p><strong>Skills:<br></strong> {{ character['skills'] }}</p>
    <p><strong>Equipment:<br></strong> {{ character['equipment'] }}</p>
    <p><strong>Mercenary:<br></strong> {{ character['mercenary'] }} - {{ character['mercenary_equipment'] }}</p>

    <div class="character-section" data-character-name="{{ character['name'] }}"></div>
</div>
<hr color="#141414">
<br>
{% endfor %}
            <br>
            </div>
            </div>
        <!--    <hr width="90%"> -->
            <br>
                {% endfor %}
            </ul>
            <br>
            <hr>
            <br>
        <p class="indented-skills">Popular builds include:<br>{{ summary_label }} </p>
            <br>
            </div>
            <br><br>
                    <!-- Embed the Plotly pie chart -->
        <div>
            <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
        </div>

        <!-- Embed the Plotly scatter plot -->
        <div>
            <img src="charts/{{ what_class }}-clusters_with_avg_points.png" alt="{{ what_class }} Skill Clusters Scatter Plot">
        </div>
        <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>
            <div class="footer">
            <p>PoD data current as of {{ timeStamp }}</p>
            </div>
        



<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}


//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}


document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});

document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});

document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>



    </body>
    </html>
    """

    def analyze_mercenaries(characters):
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        for char_data in characters:
            if not isinstance(char_data, dict):
                print(f"Skipping unexpected data format: {char_data}")
                continue  # Skip invalid entries

            mercenary = char_data.get("MercenaryType")
            if mercenary:
                readable_mercenary, _ = map_readable_names(mercenary, "")
                mercenary_counts[readable_mercenary] += 1

                for item in char_data.get("MercenaryEquipped", []):
                    worn_category = item.get("Worn", "Unknown")
                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                    title = item.get("Title", "Unknown")
                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1

        return mercenary, mercenary_counts, mercenary_equipment

    # Assuming df is your DataFrame and skill_columns contains the column names for the skills

    # Calculate the total usage of each skill across all clusters
    total_skill_usage = df[skill_columns].sum()

    # Sort skills by total usage in descending order
    most_used_skills = total_skill_usage.sort_values(ascending=False)

    # Sort skills by total usage in ascending order
    least_used_skills = total_skill_usage.sort_values(ascending=True)

    # Extract the top 5 most used skills
    top_5_most_used_skills = most_used_skills.head(5)

    # Extract the bottom 5 least used skills
    bottom_5_least_used_skills = least_used_skills.head(5)


    # Calculate the percentage of characters that have invested in each skill within the cluster
    skill_percentages = df[skill_columns].astype(bool).groupby(df['Cluster']).mean() * 100

    # Identify the top skills per cluster with their average points and percentages
    top_skills_with_avg_and_percent = skill_averages.apply(lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    summary_label = ""
    summaries = []
    data_folder = "sc/ladder-all"
    # Generate the cluster labels
    cluster_labels = {cluster: f"{cluster} users favor the skills: " + ", ".join([f"{skill} ({avg}%)" for skill, avg in skills]) for cluster, skills in top_skills_with_avg.items()}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Combine summaries into a single string
    summary_label = "<br>".join(df['Cluster_Label'].unique())

    # Gather data for the report
    clusters = {}
    for cluster, group in df.groupby('Cluster'):
        sorted_group = group.sort_values(by='Level', ascending=False)  # Sort by level descending
        character_count = len(sorted_group)
        cluster_percentage = cluster_counts[cluster]
        equipment_counts = {}
        for row in sorted_group.itertuples():
            equipment_list = row.Equipment.split(", ")
            for item in equipment_list:
                if item:
                    worn, title_count = item.split(": ", 1)
                    if " x" in title_count:
                        title, count = title_count.split(" x", 1)
                        count = int(count)
                    else:
                        title = title_count
                        count = 1

                    if worn not in equipment_counts:
                        equipment_counts[worn] = {}
                    if title in equipment_counts[worn]:
                        equipment_counts[worn][title] += count
                    else:
                        equipment_counts[worn][title] = count  # Initialize with real count
        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)

        # Generate HTML report for mercenaries in this cluster
        merc_count = f"<h3>Mercenary Equipment Analysis for Cluster {cluster}</h3>"

        # Mercenary type counts
        merc_count += "<h4>Count of Mercenary Types</h4>"
        for mercenary, count in mercenary_counts.items():
            merc_count += f"<p>{mercenary}: {count}</p>"

        # Mercenary equipment titles
        merc_count += "<h4>Equipment Titles</h4>"
        for mercenary, equipment in mercenary_equipment.items():
            merc_count += f"<p><strong>{mercenary}:</strong></p>"
            for title, count in equipment.items():
                merc_count += f"<p>{title}: {count}</p>"

        # ✅ Fix: Ensure the cluster exists before adding merc_count
        if cluster not in clusters:
            clusters[cluster] = {}

        if 'merc_count' not in clusters[cluster]:
            clusters[cluster]['merc_count'] = merc_count


        # Calculate total counts for each category
        total_counts = {
            worn: sum(titles.values())
            for worn, titles in equipment_counts.items()
        }

        # Calculate the percentages based on total counts
        equipment_percentages = {
            worn: {title: (count / total_counts[worn]) * 100 for title, count in titles.items()}
            for worn, titles in equipment_counts.items()
        }

        # Get top equipment based on count
        top_equipment = {
            worn: sorted(titles.items(), key=lambda item: item[1], reverse=True)[:5]
            for worn, titles in equipment_counts.items()
        }

        # Use equipment_percentages for display
        top_equipment_str_list = []
        for worn, titles in top_equipment.items():
            titles_str = "<br>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;{title} {equipment_percentages[worn][title]:.2f}% ({count})" for title, count in titles])
            top_equipment_str_list.append(f"<strong>{worn.capitalize()}</strong>: <br>{titles_str}")

        top_equipment_str = "<br>".join(top_equipment_str_list)

        # Use sorted_equipment_counts for full display
        sorted_equipment_counts = {
            worn: dict(sorted(titles.items(), key=lambda item: item[1], reverse=True))
            for worn, titles in equipment_counts.items()
        }

        equipment_counts_str_list = []
        for worn, titles in sorted_equipment_counts.items():
            titles_str = ", ".join([f"{title} {equipment_percentages[worn][title]:.2f}%" for title in titles])
            equipment_counts_str_list.append(f"<strong>{worn.capitalize()}</strong>: {titles_str}")

        equipment_counts_str = "<br>".join(equipment_counts_str_list)


        # Define a helper function to format numbers
        def format_number(num):
            return int(num) if num % 1 == 0 else round(num, 2)

        # Filter top skills
        top_skills = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]

        # Filter other skills, ignoring those with zero points
        other_skills = skill_averages.loc[cluster].drop(top_skills)
        other_skills = other_skills[other_skills > 0].nlargest(6)
        other_skills_pie = "<br>".join([f"{skill} ({format_number(avg)})" for skill, avg in other_skills.items()])
#        other_skills_str = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(other_skills[skill] * character_count)})" for skill in other_skills.index])
        other_skills_str = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(other_skills[skill] * character_count)})</span>"
            for skill in other_skills.index
        ])

        # Filter remaining skills, ignoring those with zero points
        remaining_skills = skill_averages.loc[cluster].sort_values(ascending=False)
        remaining_skills = remaining_skills[remaining_skills > 0]
#        remaining_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str2 = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(remaining_skills[skill] * character_count)})</span>"
            for skill in remaining_skills.index
        ])
#        remaining_skills_str_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str_with_icons = "\n".join([
            "<div class='skills-group'>" + "\n".join([
                "<div class='skills-row'>" +
                "\n".join([
                    f"<div class='skill-item'>"
                    f"<div class='skillbar-container'>"
                    f"<div class='skill-info'>"
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                    f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})"
                    f"</div>"
                    f"<div class='skill-mini-bar' style='width: {round(skill_percentages.loc[cluster, skill], 2) * 4}px;'></div>"
                    f"</div>"
                    f"</div>"
                    for skill in remaining_skills.index[row:row+2]
                ]) +
                "</div>"  # Close row
                for row in range(i, min(i+10, len(remaining_skills.index)), 2)
            ]) + "</div>"  # Close group
            for i in range(0, len(remaining_skills.index), 10)
        ])

        # Generate summaries for each unique Cluster_Label
        unique_cluster_labels = df['Cluster_Label'].unique()

        summaries = []
        data_folder = "sc/ladder-all"
        for cluster_label in unique_cluster_labels:
            # Get the rows corresponding to the current cluster label
            cluster_data = df[df['Cluster_Label'] == cluster_label]
            
            # Extract summary labels (e.g., top skills or other details you want to include)
            summary_labels = cluster_data['Skills'].unique()  # Adjust this based on what summary_labels should contain
            
            # Create summary string
            summary = f"{cluster_label} favor the skills " + ", ".join(summary_labels)
            summaries.append(summary)

        # Output results (example: print summaries)
#        for summary in summaries:
#            print(summary)

        clusters[cluster] = {
    #        'label': f"{cluster_percentage:.2f}% of {what_class}'s: <br>" + "<br>".join([f"{skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
#            'label': f"{cluster} make up {cluster_percentage:.2f}%  of Unique Projectiles in use <br>Most popular skills used by characters with them equipped:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
            'label': f"{cluster_percentage:.2f}% of Unique Arrows and Bolts are {cluster}:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar">
                                <span class="skill-label">{skill} ({int(avg * character_count)})</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
                for skill, avg, percent in top_skills_with_avg_and_percent[cluster]
            ]),
            'character_count': character_count,
            'other_skills': other_skills_str,
            'other_skills_pie': other_skills_pie,
            'characters': [{'name': row.Name, 'level': row.Level, 'skills': row.Skills, 'equipment': row.Equipment, 'mercenary': row.Mercenary, 'mercenary_equipment': row.MercenaryEquipment, 'class': row.Class } for row in sorted_group.itertuples()],
            'top_equipment': top_equipment_str,  # Add top equipment to the data
            'equipment_counts': equipment_counts_str,
            'remaining_skills_with_icons': remaining_skills_str_with_icons,
            'remaining_skills_str2': remaining_skills_str2,  # Add remaining skills string for display without icons
    #        'all_skills_str2': all_skills_str2,
    #        'all_skills_str2_with_icons' : all_skills_str2_with_icons
            'top_5_most_used_skills': top_5_most_used_skills,
            'bottom_5_least_used_skills': bottom_5_least_used_skills,
            'summary_label' : summary_label, 
            'Cluster_labels' : cluster_labels,            
            'mercenary': mercenary,  # Store mercenary type
            'mercenary_equipment': mercenary_equipment,  # Store mercenary's items
            
        }
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)


    # Ensure the correct percentage values are used
    pie_data = df.groupby('Cluster').agg({
        'Percentage': 'mean',  # Get the mean percentage for each cluster
        'Cluster_Label': 'first'  # Use the first cluster label as representative
    }).reset_index()

    # Include other_skills in customdata
#    pie_data['other_skills_pie'] = pie_data['Cluster'].map(lambda cluster: clusters[cluster]['other_skills_pie'])

    # Combine cluster label and percentage for the pie chart labels
    pie_data['Cluster_Label_Percentage'] = pie_data.apply(lambda row: f"{row['Percentage']:.2f}% ({clusters[row['Cluster']]['character_count']}) - {row['Cluster']}", axis=1)

    # Create a pie chart
    fig_pie = px.pie(
        pie_data,
        values='Percentage',  # Use the correct percentage values
        names='Cluster_Label_Percentage',
        title=f"Unique Projectile Usage",
        hover_data={'Cluster_Label': True} #, 'other_skills_pie': True}
    )

    # Update customdata to pass Cluster_Label
    fig_pie.update_traces(customdata=pie_data[['Cluster_Label']]) #, 'other_skills_pie']])

    # Customize the hover template for the pie chart
    fig_pie.update_traces(
        textinfo='percent',  # Keep percentages on the pie slices
        textposition='inside',  # Position percentages inside the pie slices
        pull=[0.05] * len(pie_data),  # Slightly pull slices apart to increase visibility
    )

    # Position the legend outside the pie chart and adjust the pie chart size
    fig_pie.update_layout(
        legend=dict(
            x=250,  # Position the legend to the right
            y=1,  # Center the legend vertically
            traceorder='normal',
            font=dict(size=10, color='white'),
            bgcolor='rgba(0,0,0,0)',
        ),
        paper_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='white'),  # ✅ Makes all text white
        title=dict(font=dict(color='white')),  # ✅ Ensures title is also white
        margin=dict(l=0, r=0, t=50, b=0),  # Remove extra margins
        width=800,  # Set the width of the entire chart
        height=400,  # Set the height of the entire chart
    )

    # Save the pie chart as a PNG file
    fig_pie.write_image(f"pod-stats/charts/{what_class}-clusters_distribution_pie.png")


    # Sort clusters by percentage in descending order
    sorted_clusters = dict(sorted(clusters.items(), key=lambda item: item[1]['character_count'], reverse=True))


    # Ensure the cluster exists before adding merc_count
    if cluster not in clusters:
        clusters[cluster] = {}

    clusters[cluster]['merc_count'] = merc_count

#    print(f"✅ Added merc data for cluster {cluster}:")
#    print(merc_count)

    dt = datetime.now()
    # format it to a string
    timeStamp = dt.strftime('%Y-%m-%d %H:%M')

    # Render the HTML report
    template = Template(html_template)
    html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, timeStamp=timeStamp)  # Pass sorted clusters to the template

    # Save the report to a file
    output_file = f"pod-stats/{what_class}.html"
    with open(output_file, "w") as file:
        file.write(html_content)

    print(f"Cluster analysis report saved to {output_file}")

#GetUniqueProjectiles()

###############################################################
#
# Get Bong and Warpspear 
#
import requests
import os
import time
# Get non zon
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import plotly.express as px
import json
import os
from jinja2 import Template

# Chargers
# Hithub push
import subprocess

from collections import defaultdict, Counter
import json
import pandas as pd

def GetBong():
    icons_folder = "icons"
    what_class = "Bong_and_Warpspear"
    search_tags = {"The Iron Jang Bong", "Warpspear"}  # ✅ Use a set for faster lookups
    howmany_clusters = 2
    howmany_skills = 4

    # ✅ Load consolidated JSON
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)

    # ✅ Filter characters who have the item equipped
    filtered_characters = []
    for char_data in all_characters:
        if not isinstance(char_data, dict):
            continue
        
        # Add columns with default 0
        char_data["The Iron Jang Bong"] = 0
        char_data["Warpspear"] = 0

        for item in char_data.get("Equipped", []):
            if item.get("Title") == "The Iron Jang Bong":
                char_data["The Iron Jang Bong"] = 1
            elif item.get("Title") == "Warpspear":
                char_data["Warpspear"] = 1

        # Only add character if they have one of the items
        if char_data["The Iron Jang Bong"] or char_data["Warpspear"]:
            filtered_characters.append(char_data)

    def map_readable_names(mercenary_type, worn_category=""):
        mercenary_mapping = {
            "Desert Mercenary": "Act 2 Desert Mercenary",
            "Rogue Scout": "Act 1 Rogue Scout",
            "Eastern Sorceror": "Act 3 Eastern Sorceror",
            "Barbarian": "Act 5 Barbarian"
        }
        worn_mapping = {
            "body": "Armor",
            "helmet": "Helmet",
            "weapon1": "Weapon",
            "weapon2": "Offhand"
        }
        readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
        readable_worn = worn_mapping.get(worn_category, worn_category)
        return readable_mercenary, readable_worn

    def load_data(filtered_characters):
        all_data = []
        quality_colors = {
            "q_runeword": "#edcd74",
            "q_unique": "#edcd74",
            "q_set": "#45a823",
            "q_magic": "#7074c9",
            "q_rare": "yellow",
            "q_crafted": "orange"
        }

        for char_data in filtered_characters:
            if "SkillTabs" in char_data and "Equipped" in char_data:
                skill_data = {
                    "Name": char_data.get("Name", "Unknown"),
                    "Class": char_data.get("Class", "Unknown"),
                    "Level": char_data.get("Stats", {}).get("Level", "Unknown"),
                    "The Iron Jang Bong": char_data["The Iron Jang Bong"],  # ✅ Keep filtered data
                    "Warpspear": char_data["Warpspear"],  # ✅ Keep filtered data
                }

                # ✅ Extract and sort skills
                skills = []
                for tab in char_data.get('SkillTabs', []):
                    for skill in tab.get('Skills', []):
                        skill_name = skill['Name']
                        skill_level = skill['Level']
                        skill_data[skill_name] = skill_level  # ✅ Creates a separate column for each skill
                        skills.append((skill_name, skill_level))

                skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                skill_data["Skills"] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])

                # ✅ Process equipment
                equipment_titles = defaultdict(Counter)
                for item in char_data["Equipped"]:
                    worn_category = item.get("Worn", "Unknown")
                    title = item.get("Title", "Unknown")
                    quality_code = item.get("QualityCode", "default")
                    tag = item.get("Tag", "")

                    # ✅ Standardize worn category names
                    worn_category = {
                        "ring1": "Ring", "ring2": "Ring",
                        "sweapon1": "Left hand", "weapon1": "Left hand",
                        "sweapon2": "Offhand", "weapon2": "Offhand",
                        "body": "Armor", "gloves": "Gloves",
                        "belt": "Belt", "helmet": "Helmet",
                        "boots": "Boots", "amulet": "Amulet"
                    }.get(worn_category, worn_category)

                    # ✅ Set colored title
                    color = quality_colors.get(quality_code, "white")
                    if quality_code in ["q_magic", "q_rare", "q_crafted"]:
                        formatted_tag = f" {tag}" if tag else ""  # Avoids extra space if `tag` is empty
                        colored_title = f"<span style='color: {color};'>{quality_code.split('_')[1].capitalize()}{formatted_tag}</span>"
                    else:
                        colored_title = f"<span style='color: {color};'>{title}</span>"

                    equipment_titles[worn_category][colored_title] += 1

                # ✅ Convert equipment data to a readable string
                skill_data["Equipment"] = ", ".join([
                    f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                    for worn, titles in equipment_titles.items()
                    for title, count in titles.items()
                ])

                # ✅ Process mercenary info
                mercenary_type = char_data.get("MercenaryType", "No mercenary")
                readable_mercenary, _ = map_readable_names(mercenary_type)
                mercenary_equipment = ", ".join(
                    [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                ) if char_data.get("MercenaryEquipped") else "No equipment"

                skill_data["Mercenary"] = readable_mercenary
                skill_data["MercenaryEquipment"] = mercenary_equipment

                all_data.append(skill_data)

        return pd.DataFrame(all_data).fillna(0)  # ✅ Fill missing skills with 0

    # ✅ Load the data
    df = load_data(filtered_characters)#    return df  # ✅ Ensure function returns the DataFrame

    # Define skill columns (exclude non-skill columns)
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment'] + list(search_tags)]
    print("🔍 Sample DataFrame:\n", df.head())

    print("🧐 Checking columns:", df.columns)
    print("🔍 Unique values in 'The Iron Jang Bong':", df.get("The Iron Jang Bong", pd.Series()).unique())
    print("🔍 Unique values in 'Warpspear':", df.get("Warpspear", pd.Series()).unique())

#    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment'] + search_tags]

   # Create clusters based on item presence
    df["Cluster"] = df.apply(
        lambda row: "The Iron Jang Bong" if row["The Iron Jang Bong"] > 0
        else ("Warpspear" if row["Warpspear"] > 0 else "Other"), axis=1
    )
#    print("📝 DataFrame Columns:", df.columns)
#    print("🔍 Sample Data:", df.head())

    # Group by clusters and count characters
    cluster_counts = df.groupby("Cluster")["Name"].count()

    # Calculate the average points invested in skills per cluster
    df['Total_Points'] = df[skill_columns].sum(axis=1)
    cluster_averages = df.groupby('Cluster')['Total_Points'].mean().reset_index()
    cluster_averages.columns = ['Cluster', 'Avg_Points']

    # Merge the averages back into the main DataFrame
    df = pd.merge(df, cluster_averages, on='Cluster')

    # Get skill averages per cluster
    skill_averages = df.groupby('Cluster')[skill_columns].mean()

    # Identify the top skills per cluster with their average points
    top_skills_with_avg = skill_averages.apply(lambda x: [(skill, round(x[skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    # Calculate the correct percentages for each cluster
    cluster_counts = df['Cluster'].value_counts(normalize=True) * 100
    df['Percentage'] = df['Cluster'].map(cluster_counts)

    # Map clusters to meaningful names (top skills with average points)
    cluster_labels = {cluster: f"{cluster} users favor the skills " + ", ".join([f"{skill} {avg:.2f}%" for skill, avg in skills]) for cluster, skills in top_skills_with_avg.items()}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Updated HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ what_class }} Analysis Report</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

    </head>
    <body class="not-main">

        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>

            <h1>Warpspear and The Iron Jang Bong Usage </h1>
            <div class="summary-container">
                <br>
        <h3>This is characters who have Warpspear or The Iron Jang Bong equipped</h3>
            
            <p class="indented-skills"> </p>


<!--        <h2>Detailed Grouping Information, Ordered Highest to Lowest %</h2>-->

        {% for clusters, data in clusters.items() %}
        <!--<h2>{{ data['label'] }}</h2>
        <p class="indented-skills"><strong>Other Skills:<br></strong> {{ data['other_skills'] }}</p> -->
        <div class="class-intro">
        <div id="skills" class="skills-container">
            <div class="column">
                <ul id="most-popular-skills">
                    <h2>{{ data['label'] }}</h2>
                </ul>
            </div>
<!--            <div class="column">
                <ul id="other-skills">
                    <h2>Other common skills in this group:</h2> {{ data['other_skills'] }}
                </ul>
            </div> -->
        </div>

    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>All Skills</strong></button>
                <div class="content">
                    <div>{{ data['remaining_skills_with_icons'] }}</div>
                </div>

                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>Most Common Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['top_equipment'] }}</div>
                </div>
<!--            
                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>ALL Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['equipment_counts'] }}</div>
                </div>
-->
            <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>{{ data['character_count'] }} Characters in this cluster:</strong>
        </button>
        <div class="content">
{% for character in data['characters'] %}
<!--
<div class="character-container {% if loop.index is even %}char1{% else %}char2{% endif %}">
-->
<div class="character-container char2">
    <div class="character-info">
        <div class="character-link"><strong>Name: <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}
            </a></strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="hover-trigger" data-character-name="{{ character['name'] }}">
            <!-- Armory Quickview -->
        </div>
    </div>

    <div class="character">
        <div class="popup hidden"></div> <!-- No iframe inside initially -->
    </div>

    <p><strong>Skills:<br></strong> {{ character['skills'] }}</p>
    <p><strong>Equipment:<br></strong> {{ character['equipment'] }}</p>
    <p><strong>Mercenary:<br></strong> {{ character['mercenary'] }} - {{ character['mercenary_equipment'] }}</p>

    <div class="character-section" data-character-name="{{ character['name'] }}"></div>
</div>
<hr color="#141414">
<br>
{% endfor %}
            <br>
            </div>
            </div>
        <!--    <hr width="90%"> -->
            <br>
            {% endfor %}
                <h3>Top 5 Most Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in top_5_most_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>

            <h3>Bottom 5 Least Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in bottom_5_least_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>
            <br>
            <hr>
            <br>
        <p class="indented-skills">Popular builds include:<br>{{ summary_label }} </p>
            <br>
            </div>
            <br><br>
                    <!-- Embed the Plotly pie chart -->
<!--            <div>
                <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
            </div> 
-->
            <!-- Embed the Plotly scatter plot -->
<!--            <div>
                <img src="charts/{{ what_class }}-clusters_with_avg_points.png" alt="{{ what_class }} Skill Clusters Scatter Plot">
            </div>
 -->
           <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>

            <div class="footer">
            <p>PoD class data current as of {{ timeStamp }}</p>
            </div>            
        



<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}
</script>

<script>
//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}

</script>

<script>
document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});
</script>
<script>
document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});
</script>

<script>
document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>




    </body>
    </html>
    """

    def analyze_mercenaries(characters):
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        for char_data in characters:
            if not isinstance(char_data, dict):
                print(f"Skipping unexpected data format: {char_data}")
                continue  # Skip invalid entries

            mercenary = char_data.get("MercenaryType")
            if mercenary:
                readable_mercenary, _ = map_readable_names(mercenary, "")
                mercenary_counts[readable_mercenary] += 1

                for item in char_data.get("MercenaryEquipped", []):
                    worn_category = item.get("Worn", "Unknown")
                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                    title = item.get("Title", "Unknown")
                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1

        return mercenary, mercenary_counts, mercenary_equipment

    # Assuming df is your DataFrame and skill_columns contains the column names for the skills

    # Calculate the total usage of each skill across all clusters
    total_skill_usage = df[skill_columns].sum()

    # Sort skills by total usage in descending order
    most_used_skills = total_skill_usage.sort_values(ascending=False)

    # Sort skills by total usage in ascending order
    least_used_skills = total_skill_usage.sort_values(ascending=True)

    # Extract the top 5 most used skills
    top_5_most_used_skills = most_used_skills.head(5)

    # Extract the bottom 5 least used skills
    bottom_5_least_used_skills = least_used_skills.head(5)


    # Calculate the percentage of characters that have invested in each skill within the cluster
    skill_percentages = df[skill_columns].astype(bool).groupby(df['Cluster']).mean() * 100

    # Identify the top skills per cluster with their average points and percentages
    top_skills_with_avg_and_percent = skill_averages.apply(lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    summary_label = ""
    summaries = []
#    data_folder = "sc/ladder-all"
    # Generate the cluster labels
    cluster_labels = {cluster: f"{cluster} users favor the skills: " + ", ".join([f"{skill} ({avg}%)" for skill, avg in skills]) for cluster, skills in top_skills_with_avg.items()}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Combine summaries into a single string
    summary_label = "<br>".join(df['Cluster_Label'].unique())

    # Gather data for the report
    clusters = {}
    for cluster, group in df.groupby('Cluster'):
        sorted_group = group.sort_values(by='Level', ascending=False)  # Sort by level descending
        character_count = len(sorted_group)
        cluster_percentage = cluster_counts[cluster]
        equipment_counts = {}
        for row in sorted_group.itertuples():
            equipment_list = row.Equipment.split(", ")
            for item in equipment_list:
                if item:
                    worn, title_count = item.split(": ", 1)
                    if " x" in title_count:
                        title, count = title_count.split(" x", 1)
                        count = int(count)
                    else:
                        title = title_count
                        count = 1

                    if worn not in equipment_counts:
                        equipment_counts[worn] = {}
                    if title in equipment_counts[worn]:
                        equipment_counts[worn][title] += count
                    else:
                        equipment_counts[worn][title] = count  # Initialize with real count

        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)

        # Generate HTML report for mercenaries in this cluster
        merc_count = f"<h3>Mercenary Equipment Analysis for Cluster {cluster}</h3>"

        # Mercenary type counts
        merc_count += "<h4>Count of Mercenary Types</h4>"
        for mercenary, count in mercenary_counts.items():
            merc_count += f"<p>{mercenary}: {count}</p>"

        # Mercenary equipment titles
        merc_count += "<h4>Equipment Titles</h4>"
        for mercenary, equipment in mercenary_equipment.items():
            merc_count += f"<p><strong>{mercenary}:</strong></p>"
            for title, count in equipment.items():
                merc_count += f"<p>{title}: {count}</p>"

        # ✅ Fix: Ensure the cluster exists before adding merc_count
        if cluster not in clusters:
            clusters[cluster] = {}

        if 'merc_count' not in clusters[cluster]:
            clusters[cluster]['merc_count'] = merc_count

        # Calculate total counts for each category
        total_counts = {
            worn: sum(titles.values())
            for worn, titles in equipment_counts.items()
        }

        # Calculate the percentages based on total counts
        equipment_percentages = {
            worn: {title: (count / total_counts[worn]) * 100 for title, count in titles.items()}
            for worn, titles in equipment_counts.items()
        }

        # Get top equipment based on count
        top_equipment = {
            worn: sorted(titles.items(), key=lambda item: item[1], reverse=True)[:5]
            for worn, titles in equipment_counts.items()
        }

        # Use equipment_percentages for display
        top_equipment_str_list = []
        for worn, titles in top_equipment.items():
            titles_str = "<br>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;{title} {equipment_percentages[worn][title]:.2f}% ({count})" for title, count in titles])
            top_equipment_str_list.append(f"<strong>{worn.capitalize()}</strong>: <br>{titles_str}")

        top_equipment_str = "<br>".join(top_equipment_str_list)

        # Use sorted_equipment_counts for full display
        sorted_equipment_counts = {
            worn: dict(sorted(titles.items(), key=lambda item: item[1], reverse=True))
            for worn, titles in equipment_counts.items()
        }

        equipment_counts_str_list = []
        for worn, titles in sorted_equipment_counts.items():
            titles_str = ", ".join([f"{title} {equipment_percentages[worn][title]:.2f}%" for title in titles])
            equipment_counts_str_list.append(f"<strong>{worn.capitalize()}</strong>: {titles_str}")

        equipment_counts_str = "<br>".join(equipment_counts_str_list)


        # Define a helper function to format numbers
        def format_number(num):
            return int(num) if num % 1 == 0 else round(num, 2)

        # Filter top skills
        top_skills = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]

        # Filter other skills, ignoring those with zero points
        other_skills = skill_averages.loc[cluster].drop(top_skills)
        other_skills = other_skills[other_skills > 0].nlargest(6)
        other_skills_pie = "<br>".join([f"{skill} ({format_number(avg)})" for skill, avg in other_skills.items()])
#        other_skills_str = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(other_skills[skill] * character_count)})" for skill in other_skills.index])
        other_skills_str = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(other_skills[skill] * character_count)})</span>"
            for skill in other_skills.index
        ])

        # Filter remaining skills, ignoring those with zero points
        remaining_skills = skill_averages.loc[cluster].sort_values(ascending=False)
        remaining_skills = remaining_skills[remaining_skills > 0]
#        remaining_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str2 = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(remaining_skills[skill] * character_count)})</span>"
            for skill in remaining_skills.index
        ])
#        remaining_skills_str_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str_with_icons = "\n".join([
            "<div class='skills-group'>" + "\n".join([
                "<div class='skills-row'>" +
                "\n".join([
                    f"<div class='skill-item'>"
                    f"<div class='skillbar-container'>"
                    f"<div class='skill-info'>"
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                    f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})"
                    f"</div>"
                    f"<div class='skill-mini-bar' style='width: {round(skill_percentages.loc[cluster, skill], 2) * 4}px;'></div>"
                    f"</div>"
                    f"</div>"
                    for skill in remaining_skills.index[row:row+2]
                ]) +
                "</div>"  # Close row
                for row in range(i, min(i+10, len(remaining_skills.index)), 2)
            ]) + "</div>"  # Close group
            for i in range(0, len(remaining_skills.index), 10)
        ])

        # Generate summaries for each unique Cluster_Label
        unique_cluster_labels = df['Cluster_Label'].unique()

        summaries = []
#        data_folder = "sc/ladder-all"
        for cluster_label in unique_cluster_labels:
            # Get the rows corresponding to the current cluster label
            cluster_data = df[df['Cluster_Label'] == cluster_label]
            
            # Extract summary labels (e.g., top skills or other details you want to include)
            summary_labels = cluster_data['Skills'].unique()  # Adjust this based on what summary_labels should contain
            
            # Create summary string
            summary = f"{cluster_label} favor the skills " + ", ".join(summary_labels)
            summaries.append(summary)
            



        clusters[cluster] = {
#            'label': f"{cluster} users:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
#            'label': f"{cluster_percentage:.2f}% of {cluster} {what_class}'s Main Skills:<br>" + "".join([
            'label': f"{cluster} users Main Skills:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar">
                                <span class="skill-label">{skill} ({int(avg * character_count)})</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
                for skill, avg, percent in top_skills_with_avg_and_percent[cluster]
            ]),
            'character_count': character_count,
            'other_skills': other_skills_str,
            'other_skills_pie': other_skills_pie,
            'characters': [{'name': row.Name, 'level': row.Level, 'skills': row.Skills, 'equipment': row.Equipment, 'mercenary': row.Mercenary, 'mercenary_equipment': row.MercenaryEquipment, 'class': row.Class } for row in sorted_group.itertuples()],
            'top_equipment': top_equipment_str,  # Add top equipment to the data
            'equipment_counts': equipment_counts_str,
            'remaining_skills_with_icons': remaining_skills_str_with_icons,
            'remaining_skills_str2': remaining_skills_str2,  # Add remaining skills string for display without icons
            'top_5_most_used_skills': top_5_most_used_skills,
            'bottom_5_least_used_skills': bottom_5_least_used_skills,
            'summary_label' : summary_label, 
            'Cluster_labels' : cluster_labels,
            'mercenary': mercenary,  # Store mercenary type
            'mercenary_equipment': mercenary_equipment,  # Store mercenary's items
            
        }
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)


    # Ensure the correct percentage values are used
    pie_data = df.groupby('Cluster').agg({
        'Percentage': 'mean',  # Get the mean percentage for each cluster
        'Cluster_Label': 'first'  # Use the first cluster label as representative
    }).reset_index()

    # Include other_skills in customdata
    pie_data['other_skills_pie'] = pie_data['Cluster'].map(lambda cluster: clusters[cluster]['other_skills_pie'])

    # Combine cluster label and percentage for the pie chart labels
    pie_data['Cluster_Label_Percentage'] = pie_data.apply(lambda row: f"{row['Percentage']:.2f}% - Main Skills and avg points: {row['Cluster_Label']}", axis=1)

    # Create a pie chart
    fig_pie = px.pie(
        pie_data,
        values='Percentage',  # Use the correct percentage values
        names='Cluster_Label_Percentage',
        title=f"{what_class} Skills Distribution",
        hover_data={'Cluster_Label': True, 'other_skills_pie': True}
    )

    # Update customdata to pass Cluster_Label
    fig_pie.update_traces(customdata=pie_data[['Cluster_Label', 'other_skills_pie']])

    # Customize the hover template for the pie chart
    fig_pie.update_traces(
        textinfo='percent',  # Keep percentages on the pie slices
        textposition='inside',  # Position percentages inside the pie slices
        hovertemplate="<b>%{customdata[0]}</b><br>Other Skills and Average Point Investment:<br>%{customdata[1]}<extra></extra>",
    )

    # Position the legend outside the pie chart and adjust the pie chart size
    fig_pie.update_layout(
        legend=dict(
            x=1.05,  # Position the legend to the right
            y=0.5,  # Center the legend vertically
            traceorder='normal',
            font=dict(
                size=10,
            ),
        ),
        margin=dict(l=0, r=0, t=50, b=0),  # Remove extra margins
        width=800,  # Set the width of the entire chart
        height=400,  # Set the height of the entire chart
    )

    # Save the pie chart as a PNG file
    fig_pie.write_image(f"pod-stats/charts/{what_class}-clusters_distribution_pie.png")

    # Create a DataFrame for visualization


    # Sort clusters by percentage in descending order
    sorted_clusters = dict(sorted(clusters.items(), key=lambda item: item[1]['character_count'], reverse=True))

    # Ensure the cluster exists before adding merc_count
    if cluster not in clusters:
        clusters[cluster] = {}

    clusters[cluster]['merc_count'] = merc_count

#    print(f"✅ Added merc data for cluster {cluster}:")
#    print(merc_count)

    dt = datetime.now()
    # format it to a string
    timeStamp = dt.strftime('%Y-%m-%d %H:%M')

    # Render the HTML report
    template = Template(html_template)
    html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, timeStamp=timeStamp)  # Pass sorted clusters to the template

    # Save the report to a file
    output_file = f"pod-stats/{what_class}.html"
    with open(output_file, "w") as file:
        file.write(html_content)

    print(f"Cluster analysis report saved to {output_file}")

#GetBong()


###############################################################
#
# Chargers????
#
# Define search criteria
def GetChargers():

    icons_folder = "icons"
    what_class = "Charge"
    howmany_clusters = 5
    howmany_skills = 4

    search_item = "Templar's Might"
    search_skill = "Charge"
    skill_threshold = 3

    # ✅ Load consolidated JSON
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)

    # ✅ Filter characters who meet the conditions
    filtered_characters = []
    for char_data in all_characters:
        if not isinstance(char_data, dict):
            continue

        # Check if they meet the Charge skill threshold
        has_high_charge = any(
            skill.get("Name") == search_skill and skill.get("Level", 0) >= skill_threshold
            for tab in char_data.get("SkillTabs", [])
            for skill in tab.get("Skills", [])
        )

        # Check if they are wearing "Templar's Might"
        has_templars_might = any(
            item.get("Title") == search_item for item in char_data.get("Equipped", [])
        )

        if has_high_charge or has_templars_might:
            filtered_characters.append(char_data)

        def map_readable_names(mercenary_type, worn_category=""):
            mercenary_mapping = {
                "Desert Mercenary": "Act 2 Desert Mercenary",
                "Rogue Scout": "Act 1 Rogue Scout",
                "Eastern Sorceror": "Act 3 Eastern Sorceror",
                "Barbarian": "Act 5 Barbarian"
            }
            worn_mapping = {
                "body": "Armor",
                "helmet": "Helmet",
                "weapon1": "Weapon",
                "weapon2": "Offhand"
            }
            readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
            readable_worn = worn_mapping.get(worn_category, worn_category)
            return readable_mercenary, readable_worn

    # ✅ Function to process data
    def load_data(filtered_characters):
        all_data = []
        quality_colors = {
            "q_runeword": "#edcd74",
            "q_unique": "#edcd74",
            "q_set": "#45a823",
            "q_magic": "#7074c9",
            "q_rare": "yellow",
            "q_crafted": "orange"
        }

        for char_data in filtered_characters:
            skill_data = {
                "Name": char_data.get("Name", "Unknown"),
                "Class": char_data.get("Class", "Unknown"),
                "Level": char_data.get("Stats", {}).get("Level", "Unknown")
            }

            # ✅ Extract and sort skills
            skills = []
            for tab in char_data.get("SkillTabs", []):
                for skill in tab.get("Skills", []):
                    skill_name = skill["Name"]
                    skill_level = skill["Level"]
                    skill_data[skill_name] = skill_level
                    skills.append((skill_name, skill_level))

            skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
            skill_data["Skills"] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])

            # ✅ Process equipment
            equipment_titles = defaultdict(Counter)
            for item in char_data.get("Equipped", []):
                worn_category = item.get("Worn", "Unknown")
                title = item.get("Title", "Unknown")
                quality_code = item.get("QualityCode", "default")

                # ✅ Standardize worn category names
                worn_category = {
                    "ring1": "Ring", "ring2": "Ring",
                    "sweapon1": "Left hand", "weapon1": "Left hand",
                    "sweapon2": "Offhand", "weapon2": "Offhand",
                    "body": "Armor", "gloves": "Gloves",
                    "belt": "Belt", "helmet": "Helmet",
                    "boots": "Boots", "amulet": "Amulet"
                }.get(worn_category, worn_category)

                # ✅ Set colored title
                color = quality_colors.get(quality_code, "white")
                colored_title = f"<span style='color: {color};'>{title}</span>"

                equipment_titles[worn_category][colored_title] += 1

            # ✅ Convert equipment data to a readable string
            skill_data["Equipment"] = ", ".join([
                f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                for worn, titles in equipment_titles.items()
                for title, count in titles.items()
            ])

            # ✅ Process mercenary info
            mercenary_type = char_data.get("MercenaryType", "No mercenary")
            readable_mercenary = {
                "Desert Mercenary": "Act 2 Desert Mercenary",
                "Rogue Scout": "Act 1 Rogue Scout",
                "Eastern Sorceror": "Act 3 Eastern Sorceror",
                "Barbarian": "Act 5 Barbarian"
            }.get(mercenary_type, mercenary_type)

            mercenary_equipment = ", ".join(
                [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
            ) if char_data.get("MercenaryEquipped") else "No equipment"

            skill_data["Mercenary"] = readable_mercenary
            skill_data["MercenaryEquipment"] = mercenary_equipment

            all_data.append(skill_data)

        return pd.DataFrame(all_data).fillna(0)  # ✅ Fill missing skills with 0

    # ✅ Load the DataFrame
    df = load_data(filtered_characters)

    # ✅ Define skill columns (exclude non-skill columns)
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment']]

    # ✅ Determine number of unique classes
    unique_classes = df["Class"].nunique()

    # ✅ Ensure at least 2 clusters for meaningful results
    num_clusters = max(unique_classes, 2)  # 🔹 Avoids issues with a single class
    print(f"📊 Setting n_clusters = {num_clusters}")

    # Convert Class column to one-hot encoded features
    class_encoded = pd.get_dummies(df["Class"], prefix="Class")

    # Combine skill columns with class-encoded features
    features = pd.concat([df[skill_columns], class_encoded], axis=1)

    # Perform PCA with the new feature set
    pca = PCA(n_components=2)
    reduced_data = pca.fit_transform(features)

    # Perform K-Means clustering
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    df["Cluster"] = kmeans.fit_predict(reduced_data)

    # ✅ Calculate the average points invested in skills per cluster
    df["Total_Points"] = df[skill_columns].sum(axis=1)
    cluster_averages = df.groupby("Cluster")["Total_Points"].mean().reset_index()
    cluster_averages.columns = ["Cluster", "Avg_Points"]

    # ✅ Merge the averages back into the main DataFrame
    df = pd.merge(df, cluster_averages, on="Cluster")

    # ✅ Get skill averages per cluster
    skill_averages = df.groupby("Cluster")[skill_columns].mean()

    # ✅ Identify the top skills per cluster with their average points
    top_skills_with_avg = skill_averages.apply(
        lambda x: [(skill, round(x[skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1
    )

    # ✅ Calculate the correct percentages for each cluster
    cluster_counts = df["Cluster"].value_counts(normalize=True) * 100
    df["Percentage"] = df["Cluster"].map(cluster_counts)

    # ✅ Map clusters to meaningful names (top skills with average points)
    cluster_labels = {
        cluster: f"{cluster} users favor the skills " + ", ".join([f"{skill} {avg:.2f}%" for skill, avg in skills])
        for cluster, skills in top_skills_with_avg.items()
    }
    df["Cluster_Label"] = df["Cluster"].map(cluster_labels)

    # Updated HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ what_class }} Analysis Report</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

    </head>
    <body class="not-main">

        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>


        <h1>{{ what_class }} Softcore Skill Distribution </h1>
            <div class="summary-container">
                <br>
        <h3>This group includes anyone with 3 or more points in Charge OR has Templars equipped</h3>
            
            <p class="indented-skills"> </p>


<!--        <h2>Detailed Grouping Information, Ordered Highest to Lowest %</h2>-->

        {% for clusters, data in clusters.items() %}
        <!--<h2>{{ data['label'] }}</h2>
        <p class="indented-skills"><strong>Other Skills:<br></strong> {{ data['other_skills'] }}</p> -->
        <div class="class-intro">
        <div id="skills" class="skills-container">
            <div class="column">
                <ul id="most-popular-skills">
                    <h2>{{ data['label'] }}</h2>
                </ul>
            </div>
<!--            <div class="column">
                <ul id="other-skills">
                    <h2>Other common skills in this group:</h2> {{ data['other_skills'] }}
                </ul>
            </div> -->
        </div>

    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>All Skills</strong></button>
                <div class="content">
                    <div>{{ data['remaining_skills_with_icons'] }}</div>
                </div>

                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>Most Common Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['top_equipment'] }}</div>
                </div>
<!--            
                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>ALL Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['equipment_counts'] }}</div>
                </div>
-->
            <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>{{ data['character_count'] }} Characters in this cluster:</strong>
        </button>
        <div class="content">
{% for character in data['characters'] %}
<!--
<div class="character-container {% if loop.index is even %}char1{% else %}char2{% endif %}">
-->
<div class="character-container char2">
    <div class="character-info">
        <div class="character-link"><strong>Name: <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}
            </a></strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="hover-trigger" data-character-name="{{ character['name'] }}">
            <!-- Armory Quickview -->
        </div>
    </div>

    <div class="character">
        <div class="popup hidden"></div> <!-- No iframe inside initially -->
    </div>

    <p><strong>Skills:<br></strong> {{ character['skills'] }}</p>
    <p><strong>Equipment:<br></strong> {{ character['equipment'] }}</p>
    <p><strong>Mercenary:<br></strong> {{ character['mercenary'] }} - {{ character['mercenary_equipment'] }}</p>

    <div class="character-section" data-character-name="{{ character['name'] }}"></div>
</div>
<hr color="#141414">
<br>
{% endfor %}
            <br>
            </div>
            </div>
        <!--    <hr width="90%"> -->
            <br>
            {% endfor %}
                <h3>Top 5 Most Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in top_5_most_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>

            <h3>Bottom 5 Least Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in bottom_5_least_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>
            <br>
            <hr>
            <br>
        <p class="indented-skills">Popular builds include:<br>{{ summary_label }} </p>
            <br>
            </div>
            <br><br>
                    <!-- Embed the Plotly pie chart -->
            <div>
                <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
            </div> 

            <!-- Embed the Plotly scatter plot -->
<!--            <div>
                <img src="charts/{{ what_class }}-clusters_with_avg_points.png" alt="{{ what_class }} Skill Clusters Scatter Plot">
            </div>
 -->
           <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>

            <div class="footer">
            <p>PoD class data current as of {{ timeStamp }}</p>
            </div>   
        



<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}


//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}


document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});

document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});

document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>




    </body>
    </html>
    """

    def analyze_mercenaries(characters):
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        for char_data in characters:
            if not isinstance(char_data, dict):
                print(f"Skipping unexpected data format: {char_data}")
                continue  # Skip invalid entries

            mercenary = char_data.get("MercenaryType")
            if mercenary:
                readable_mercenary, _ = map_readable_names(mercenary, "")
                mercenary_counts[readable_mercenary] += 1

                for item in char_data.get("MercenaryEquipped", []):
                    worn_category = item.get("Worn", "Unknown")
                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                    title = item.get("Title", "Unknown")
                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1

        return mercenary, mercenary_counts, mercenary_equipment

    # Assuming df is your DataFrame and skill_columns contains the column names for the skills

    # Calculate the total usage of each skill across all clusters
    total_skill_usage = df[skill_columns].sum()

    # Sort skills by total usage in descending order
    most_used_skills = total_skill_usage.sort_values(ascending=False)

    # Sort skills by total usage in ascending order
    least_used_skills = total_skill_usage.sort_values(ascending=True)

    # Extract the top 5 most used skills
    top_5_most_used_skills = most_used_skills.head(5)

    # Extract the bottom 5 least used skills
    bottom_5_least_used_skills = least_used_skills.head(5)


    # Calculate the percentage of characters that have invested in each skill within the cluster
    skill_percentages = df[skill_columns].astype(bool).groupby(df['Cluster']).mean() * 100

    # Identify the top skills per cluster with their average points and percentages
    top_skills_with_avg_and_percent = skill_averages.apply(lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    summary_label = ""
    summaries = []
    data_folder = "sc/ladder-all"

    # Gather data for the report
    clusters = {}
    for cluster, group in df.groupby('Cluster'):
        sorted_group = group.sort_values(by='Level', ascending=False)  # Sort by level descending
        character_count = len(sorted_group)
        cluster_percentage = cluster_counts[cluster]
        equipment_counts = {}
        for row in sorted_group.itertuples():
            equipment_list = row.Equipment.split(", ")
            for item in equipment_list:
                if item:
                    worn, title_count = item.split(": ", 1)
                    if " x" in title_count:
                        title, count = title_count.split(" x", 1)
                        count = int(count)
                    else:
                        title = title_count
                        count = 1

                    if worn not in equipment_counts:
                        equipment_counts[worn] = {}
                    if title in equipment_counts[worn]:
                        equipment_counts[worn][title] += count
                    else:
                        equipment_counts[worn][title] = count  # Initialize with real count

        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)

        # Generate HTML report for mercenaries in this cluster
        merc_count = f"<h3>Mercenary Equipment Analysis for Cluster {cluster}</h3>"

        # Mercenary type counts
        merc_count += "<h4>Count of Mercenary Types</h4>"
        for mercenary, count in mercenary_counts.items():
            merc_count += f"<p>{mercenary}: {count}</p>"

        # Mercenary equipment titles
        merc_count += "<h4>Equipment Titles</h4>"
        for mercenary, equipment in mercenary_equipment.items():
            merc_count += f"<p><strong>{mercenary}:</strong></p>"
            for title, count in equipment.items():
                merc_count += f"<p>{title}: {count}</p>"

        # ✅ Fix: Ensure the cluster exists before adding merc_count
        if cluster not in clusters:
            clusters[cluster] = {}

        if 'merc_count' not in clusters[cluster]:
            clusters[cluster]['merc_count'] = merc_count

        # Calculate total counts for each category
        total_counts = {
            worn: sum(titles.values())
            for worn, titles in equipment_counts.items()
        }

        # Calculate the percentages based on total counts
        equipment_percentages = {
            worn: {title: (count / total_counts[worn]) * 100 for title, count in titles.items()}
            for worn, titles in equipment_counts.items()
        }

        # Get top equipment based on count
        top_equipment = {
            worn: sorted(titles.items(), key=lambda item: item[1], reverse=True)[:5]
            for worn, titles in equipment_counts.items()
        }

        # Use equipment_percentages for display
        top_equipment_str_list = []
        for worn, titles in top_equipment.items():
            titles_str = "<br>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;{title} {equipment_percentages[worn][title]:.2f}% ({count})" for title, count in titles])
            top_equipment_str_list.append(f"<strong>{worn.capitalize()}</strong>: <br>{titles_str}")

        top_equipment_str = "<br>".join(top_equipment_str_list)

        # Use sorted_equipment_counts for full display
        sorted_equipment_counts = {
            worn: dict(sorted(titles.items(), key=lambda item: item[1], reverse=True))
            for worn, titles in equipment_counts.items()
        }

        equipment_counts_str_list = []
        for worn, titles in sorted_equipment_counts.items():
            titles_str = ", ".join([f"{title} {equipment_percentages[worn][title]:.2f}%" for title in titles])
            equipment_counts_str_list.append(f"<strong>{worn.capitalize()}</strong>: {titles_str}")

        equipment_counts_str = "<br>".join(equipment_counts_str_list)

        # Define a helper function to format numbers
        def format_number(num):
            return int(num) if num % 1 == 0 else round(num, 2)

        # Filter top skills
        top_skills = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]

        # Filter other skills, ignoring those with zero points
        other_skills = skill_averages.loc[cluster].drop(top_skills)
        other_skills = other_skills[other_skills > 0].nlargest(6)
        other_skills_pie = "<br>".join([f"{skill} ({format_number(avg)})" for skill, avg in other_skills.items()])
#        other_skills_str = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(other_skills[skill] * character_count)})" for skill in other_skills.index])
        other_skills_str = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(other_skills[skill] * character_count)})</span>"
            for skill in other_skills.index
        ])

        # Filter remaining skills, ignoring those with zero points
        remaining_skills = skill_averages.loc[cluster].sort_values(ascending=False)
        remaining_skills = remaining_skills[remaining_skills > 0]
#        remaining_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str2 = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(remaining_skills[skill] * character_count)})</span>"
            for skill in remaining_skills.index
        ])
#        remaining_skills_str_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str_with_icons = "\n".join([
            "<div class='skills-group'>" + "\n".join([
                "<div class='skills-row'>" +
                "\n".join([
                    f"<div class='skill-item'>"
                    f"<div class='skillbar-container'>"
                    f"<div class='skill-info'>"
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                    f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})"
                    f"</div>"
                    f"<div class='skill-mini-bar' style='width: {round(skill_percentages.loc[cluster, skill], 2) * 4}px;'></div>"
                    f"</div>"
                    f"</div>"
                    for skill in remaining_skills.index[row:row+2]
                ]) +
                "</div>"  # Close row
                for row in range(i, min(i+10, len(remaining_skills.index)), 2)
            ]) + "</div>"  # Close group
            for i in range(0, len(remaining_skills.index), 10)
        ])
   #    all_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
    #    all_skills_str2_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
        sorted_summary_label = ""
        summary_labels = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]
        summary = f"{cluster_percentage:.2f}% of {what_class}'s invest heavily in " + ", ".join(summary_labels)
        summaries.append((cluster_percentage, summary))

        clusters[cluster] = {
    #        'label': f"{cluster_percentage:.2f}% of {what_class}'s: <br>" + "<br>".join([f"{skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
#            'label': f"{cluster_percentage:.2f}%  of {what_class}'s Main Skills:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
            'label': f"{cluster_percentage:.2f}% of {cluster} {what_class}'s Main Skills:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar">
                                <span class="skill-label">{skill} ({int(avg * character_count)})</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
                for skill, avg, percent in top_skills_with_avg_and_percent[cluster]
            ]),
            'character_count': character_count,
            'other_skills': other_skills_str,
            'other_skills_pie': other_skills_pie,
            'characters': [{'name': row.Name, 'level': row.Level, 'skills': row.Skills, 'equipment': row.Equipment, 'mercenary': row.Mercenary, 'mercenary_equipment': row.MercenaryEquipment, 'class': row.Class } for row in sorted_group.itertuples()],
            'top_equipment': top_equipment_str,  # Add top equipment to the data
            'equipment_counts': equipment_counts_str,
            'remaining_skills_with_icons': remaining_skills_str_with_icons,
            'remaining_skills_str2': remaining_skills_str2,  # Add remaining skills string for display without icons
    #        'all_skills_str2': all_skills_str2,
    #        'all_skills_str2_with_icons' : all_skills_str2_with_icons
            'top_5_most_used_skills': top_5_most_used_skills,
            'bottom_5_least_used_skills': bottom_5_least_used_skills,
            'summary_label' : summary_label, 
            
            'mercenary': mercenary,  # Store mercenary type
            'mercenary_equipment': mercenary_equipment,  # Store mercenary's items
            
        }
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)


    # Ensure the correct percentage values are used
    pie_data = df.groupby('Cluster').agg({
        'Percentage': 'mean',  # Get the mean percentage for each cluster
        'Cluster_Label': 'first'  # Use the first cluster label as representative
    }).reset_index()

    # Include other_skills in customdata
    pie_data['other_skills_pie'] = pie_data['Cluster'].map(lambda cluster: clusters[cluster]['other_skills_pie'])

    # Combine cluster label and percentage for the pie chart labels
    pie_data['Cluster_Label_Percentage'] = pie_data.apply(lambda row: f"{row['Percentage']:.2f}% - Main Skills and avg points: {row['Cluster_Label']}", axis=1)

    import plotly.express as px

    # Get unique clusters
    unique_clusters = sorted(df['Cluster'].unique())  # Sorting ensures consistent ordering

    # Assign colors from a predefined palette
    color_palette = px.colors.qualitative.Safe  # You can change this to Vivid, Bold, etc.
    color_map = {cluster: color_palette[i % len(color_palette)] for i, cluster in enumerate(unique_clusters)}

    # Create a pie chart
    fig_pie = px.pie(
        pie_data,
        values='Percentage',
        names='Cluster_Label_Percentage',
        title=f"{what_class} Skills Distribution",
        hover_data={'Cluster_Label': True, 'other_skills_pie': True},
        color_discrete_map={row['Cluster_Label_Percentage']: color_map[row['Cluster']] for _, row in pie_data.iterrows()}  # ✅ Maps labels to the same colors
    )

    # Update customdata to pass Cluster_Label
    fig_pie.update_traces(customdata=pie_data[['Cluster_Label', 'other_skills_pie']])

    # Customize the hover template for the pie chart
    fig_pie.update_traces(
        textinfo='percent',  # Keep percentages on the pie slices
        textposition='inside',  # Position percentages inside the pie slices
        hovertemplate="<b>%{customdata[0]}</b><br>Other Skills and Average Point Investment:<br>%{customdata[1]}<extra></extra>",
        marker=dict(line=dict(color='black', width=1)),  # Add a slight outline for clarity
        pull=[0.05] * len(pie_data),  # Slightly pull slices apart to increase visibility
        hole=0  # Ensure it's a full pie (not a donut)
    )

    # Position the legend outside the pie chart and adjust the pie chart size
    fig_pie.update_layout(
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",
            y=-0.15,  # Move it closer
            xanchor="center",
            x=0.5,  # Keep it centered
            font=dict(size=10, color='white'),
            bgcolor='rgba(0,0,0,0)',
#                font=dict(color='white'),  # ✅ Transparent background
        ),
        paper_bgcolor='rgba(0,0,0,0)', # ✅ Transparent background
        margin=dict(l=10, r=10, t=50, b=20),  # Reduce bottom margin to make more space
        width=900,  # Set the width of the entire chart
        height=600,  # Set the height of the entire chart
        font=dict(color='white'),  # ✅ Makes all text white
        title=dict(font=dict(color='white')),  # ✅ Ensures title is also white
#            legend=dict(font=dict(color='white'))  # ✅ Ensures legend text is white
    )

    # Increase the pie size explicitly
    fig_pie.update_traces(domain=dict(x=[0, 1], y=[0.1, 1]))  # Expands pie upward

    # Save the pie chart as a PNG file
    fig_pie.write_image(f"pod-stats/charts/{what_class}-clusters_distribution_pie.png")

    # Create a DataFrame for visualization
    plot_data = pd.DataFrame({
        'PCA1': reduced_data[:, 0],
        'PCA2': reduced_data[:, 1],
        'Cluster': df['Cluster'],
        'Cluster_Label': df['Cluster_Label'],
        'Percentage': df['Percentage']
    })

    # Create an interactive scatter plot
    fig_scatter = px.scatter(
        plot_data,
        x='PCA1',
        y='PCA2',
        color='Cluster',  # Assign color based on the cluster
        title=f"{what_class} Skill Clusters (Ladder Top 200 {what_class}'s Highlighted)<br>This highlights how similar (or not) a character is to the rest<br>The tighter the grouping, the more they are alike",
        hover_data={'Cluster_Label': True, 'Percentage': ':.2f%', 'Cluster': True},
        color_discrete_map=color_map  # Use the same colors as the pie chart
    )

    # Customize the legend labels
    for trace in fig_scatter.data:
        if trace.name.isnumeric():  # Ensure that the trace name is numeric
            trace.update(name=legend_labels[int(trace.name)])

    # Customize hover template to include top skills and percentage
    fig_scatter.update_traces(
        hovertemplate="<b>Cluster skills and average point investment:</b><br> %{customdata[0]}<br>" +
                    "This cluster (%{customdata[2]}) makes up %{customdata[1]:.2f}% of the total<extra></extra>"
    )

    # Hide the axis titles and tick labels
    fig_scatter.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        xaxis_showticklabels=False,
        yaxis_showticklabels=False
    )

    # Save the scatter plot as a PNG file
    fig_scatter.write_image(f"pod-stats/charts/{what_class}-clusters_with_avg_points.png")

    print("Pie chart and scatter plot saved as PNG files.")


    # Sort clusters by percentage in descending order
    sorted_clusters = dict(sorted(clusters.items(), key=lambda item: item[1]['character_count'], reverse=True))

    # Split the entries into a list
    entries = summary_label.strip().split("<br>\n")
    # Remove any empty strings from the list (if any)
    entries = [entry for entry in entries if entry.strip()]
    # Sort the entries in descending order based on the percentage value
    sorted_entries = sorted(entries, key=lambda x: float(x.split('%')[0]), reverse=False)
    # Join the sorted entries back into a single string
    sorted_summaries = sorted(summaries, key=lambda x: x[0], reverse=True)
    summary_label = "<br>".join(summary for _, summary in sorted_summaries)
    #print(summary_label)

    # Ensure the cluster exists before adding merc_count
    if cluster not in clusters:
        clusters[cluster] = {}

    clusters[cluster]['merc_count'] = merc_count

#    print(f"✅ Added merc data for cluster {cluster}:")
#    print(merc_count)

    dt = datetime.now()
    # format it to a string
    timeStamp = dt.strftime('%Y-%m-%d %H:%M')

    # Render the HTML report
    template = Template(html_template)
    html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, timeStamp=timeStamp)  # Pass sorted clusters to the template

    # Save the report to a file
    output_file = f"pod-stats/{what_class}.html"
    with open(output_file, "w") as file:
        file.write(html_content)

    print(f"Cluster analysis report saved to {output_file}")

#GetChargers()

###############################################################
#
# Get chars with 2 or more offensive aura granting items
#
def GetOffensiveAuraItemsEquipped():
    icons_folder = "icons"
    what_class = "2AuraItems"
    search_tags = ["Dream", "Dragon", "Hand of Justice", "Doom", "Todesfaelle Flamme", "Azurewrath"]
    howmany_clusters = 6
    howmany_skills = 4

    # Load the consolidated JSON file
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)

    # List to store filtered characters
    filtered_characters = []

    # Process each character in the JSON
    for char_data in all_characters:
        try:
            tag_count = 0  # Initialize a counter for search tags
            for item in char_data.get("Equipped", []):  # Safely get 'Equipped' items
                if item.get("Title") in search_tags:
                    tag_count += 1
                if tag_count >= 2:
                    filtered_characters.append(char_data)
                    break  # No need to check further items for this character
        except KeyError as e:
            print(f"Missing expected key in character data: {e}")

    # Return the filtered characters
#    return filtered_characters

    def map_readable_names(mercenary_type, worn_category=""):
        mercenary_mapping = {
            "Desert Mercenary": "Act 2 Desert Mercenary",
            "Rogue Scout": "Act 1 Rogue Scout",
            "Eastern Sorceror": "Act 3 Eastern Sorceror",
            "Barbarian": "Act 5 Barbarian"
        }
        worn_mapping = {
            "body": "Armor",
            "helmet": "Helmet",
            "weapon1": "Weapon",
            "weapon2": "Offhand"
        }
        readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
        readable_worn = worn_mapping.get(worn_category, worn_category)
        return readable_mercenary, readable_worn

    # Function to load and process data
    def load_data(all_characters, search_tags):
        all_data = []

        for char_data in all_characters:
            try:
                # Ensure required keys are present
                if 'SkillTabs' in char_data and 'Equipped' in char_data:
                    skill_data = {}
                    skill_data['Name'] = char_data.get('Name', 'Unknown')
                    skill_data['Class'] = char_data.get('Class', 'Unknown')
                    skill_data['Level'] = char_data.get('Stats', {}).get('Level', 'Unknown')

                    # Flatten skill data and sort in descending order by points
                    skills = []
                    for tab in char_data['SkillTabs']:
                        for skill in tab['Skills']:
                            skill_name = skill['Name']
                            skill_level = skill['Level']
                            skill_data[skill_name] = skill_level
                            skills.append((skill_name, skill_level))
                    skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                    skill_data['Skills'] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])

                    # Flatten equipment data and count titles
                    equipment_titles = {}
                    for item in char_data['Equipped']:
                        worn_category = item['Worn']
                        title = item.get('Title', 'Unknown')
                        tag = item.get('Tag', 'Unknown')
                        quality_code = item.get('QualityCode', 'Unknown')

                        # Normalize worn categories for specific items
                        if worn_category in ['ring1', 'ring2']:
                            worn_category = 'ring'
                        elif title in ["Dream", "Dragon"] and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                            worn_category = 'Shield'
                        elif title in ["Hand of Justice", "Doom", "Todesfaelle Flamme", "Azurewrath"] and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                            worn_category = 'Weapon'
                        elif worn_category in ['sweapon1', 'weapon1']:
                            worn_category = 'Left hand'
                        elif worn_category in ['sweapon2', 'weapon2']:
                            worn_category = 'Offhand'
                        elif worn_category in ['body']:
                            worn_category = 'Armor'
                        elif worn_category in ['helmet']:
                            worn_category = 'Helmet'

                        # Apply display formatting for item quality
                        if quality_code == "q_magic":
                            title = f"<span style='color: #7074c9;'>Magic {tag}</span>"
                        elif quality_code == "q_rare":
                            title = f"<span style='color: yellow;'>Rare {tag}</span>"
                        elif quality_code == "q_crafted":
                            title = f"<span style='color: orange;'>Crafted {tag}</span>"

                        # Count items by category and title
                        if worn_category not in equipment_titles:
                            equipment_titles[worn_category] = {}
                        if title not in equipment_titles[worn_category]:
                            equipment_titles[worn_category][title] = 0
                        equipment_titles[worn_category][title] += 1

                    skill_data['Equipment'] = ", ".join([f"{worn}: {title_tag} x{count}" for worn, titles in equipment_titles.items() for title_tag, count in titles.items()])

                    # Add item presence information
                    for tag in search_tags:
                        skill_data[tag] = 1 if any(item.get('Tag') == tag and item.get('Quality') == 'Unique' for item in char_data['Equipped']) else 0

                    # Add mercenary data
                    mercenary_data = char_data.get("MercenaryType", "No mercenary")
                    readable_mercenary, _ = map_readable_names(mercenary_data)
                    mercenary_equipment = ", ".join(
                        [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                    ) if char_data.get("MercenaryEquipped") else "No equipment"

                    # Store mercenary info
                    skill_data['Mercenary'] = readable_mercenary
                    skill_data['MercenaryEquipment'] = mercenary_equipment
                    all_data.append(skill_data)
            except Exception as e:
                print(f"Error processing character data: {e}")

        return pd.DataFrame(all_data).fillna(0)

    df = load_data(filtered_characters, search_tags)

    # Define skill columns (exclude non-skill columns)
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment'] + search_tags]
#    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment'] + search_tags]

    # Filter for unique arrows and bolts only
    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [
        part.split(' x')[0] for part in eq.split(', ') 
        if any(tag in part for tag in search_tags)  # Match against known unique items
    ])
#    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [part.split(' x')[0] for part in eq.split(', ') if 'Bolts' in part or 'Arrows' in part])
#    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [part.split(' x')[0] for part in eq.split(', ') if 'Bolts' in part or 'Arrows' in part])
#    df['Title_Tag'] = df['Equipment'].apply(lambda eq: [part.split(' x')[0] for part in eq.split(', ') if ('Bolts' in part or 'Arrows' in part) and 'Unique' in part])


    # Explode the DataFrame to create one row per item
    df = df.explode('Title_Tag')


    # Remove worn category from Title_Tag
    df['Title_Tag'] = df['Title_Tag'].apply(lambda x: x.split(': ')[1] if ': ' in x else x)

    # Create clusters based on item presence (Title + Tag)
    df['Cluster'] = df['Title_Tag']
    # Ensure each character appears only once per cluster
    df = df.groupby(['Name', 'Cluster'], as_index=False).first()

    # Calculate the average points invested in skills per cluster
    df['Total_Points'] = df[skill_columns].sum(axis=1)
    cluster_averages = df.groupby('Cluster')['Total_Points'].mean().reset_index()
    cluster_averages.columns = ['Cluster', 'Avg_Points']

    # Merge the averages back into the main DataFrame
    df = pd.merge(df, cluster_averages, on='Cluster')

    # Get skill averages per cluster
    skill_averages = df.groupby('Cluster')[skill_columns].mean()

    # Identify the top skills per cluster with their average points
    top_skills_with_avg = skill_averages.apply(lambda x: [(skill, round(x[skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    # Calculate the correct percentages for each cluster
    cluster_counts = df['Cluster'].value_counts(normalize=True) * 100
    df['Percentage'] = df['Cluster'].map(cluster_counts)

    # Map clusters to meaningful names (top skills with average points)
#    cluster_labels = {i: ", ".join([f"{skill} ({avg})" for skill, avg in skills]) for i, skills in enumerate(top_skills_with_avg)}
#    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)
    cluster_labels = {cluster: f"{cluster}" for cluster in df['Cluster'].unique()}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Updated HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ what_class }} Analysis Report</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

    </head>
    <body class="not-main">

        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>

             
                
        <h1>Characters with 2 Offensive Aura items equipped </h1>
            <div class="summary-container">
                <br>
        <h3>Includes characters with any combination of two of HoJ, Dream, Dragon, Doom, Azurewrath, or Todesfaelle's <br>{{ filtered_file_count }} Characters total</h3>
            
            <p class="indented-skills"> </p>


<!--        <h2>Detailed Grouping Information, Ordered Highest to Lowest %</h2>-->

        {% for clusters, data in clusters.items() %}
        <!--<h2>{{ data['label'] }}</h2>
        <p class="indented-skills"><strong>Other Skills:<br></strong> {{ data['other_skills'] }}</p> -->
        <div class="class-intro">
        <div id="skills" class="skills-container">
            <div class="column">
                <ul id="most-popular-skills">
                    <h2>{{ data['label'] }}</h2>
                </ul>
            </div>
<!--            <div class="column">
                <ul id="other-skills">
                    <h2>Other common skills in this group:</h2> {{ data['other_skills'] }}
                </ul>
            </div> -->
        </div>

    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>All Skills</strong></button>
                <div class="content">
                    <div>{{ data['remaining_skills_with_icons'] }}</div>
                </div>

                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>Most Common Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['top_equipment'] }}</div>
                </div>
<!--            
                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>ALL Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['equipment_counts'] }}</div>
                </div>
-->
            <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>{{ data['character_count'] }} Characters in this cluster:</strong>
        </button>
        <div class="content">
{% for character in data['characters'] %}
<!--
<div class="character-container {% if loop.index is even %}char1{% else %}char2{% endif %}">
-->
<div class="character-container char2">
    <div class="character-info">
        <div class="character-link"><strong>Name: <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}
            </a></strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="hover-trigger" data-character-name="{{ character['name'] }}">
            <!-- Armory Quickview -->
        </div>
    </div>

    <div class="character">
        <div class="popup hidden"></div> <!-- No iframe inside initially -->
    </div>

    <p><strong>Skills:<br></strong> {{ character['skills'] }}</p>
    <p><strong>Equipment:<br></strong> {{ character['equipment'] }}</p>
    <p><strong>Mercenary:<br></strong> {{ character['mercenary'] }} - {{ character['mercenary_equipment'] }}</p>

    <div class="character-section" data-character-name="{{ character['name'] }}"></div>
</div>
<hr color="#141414">
<br>
{% endfor %}
            <br>
            </div>
            </div>
        <!--    <hr width="90%"> -->
            <br>
            {% endfor %}
                <h3>Top 5 Most Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in top_5_most_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>

            <h3>Bottom 5 Least Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in bottom_5_least_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>
            <br>
            <hr>
            <br>
        <p class="indented-skills">Popular builds include:<br>{{ summary_label }} </p>
            <br>
            </div>
            <br><br>
                    <!-- Embed the Plotly pie chart -->
            <div>
                <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
            </div> 

            <!-- Embed the Plotly scatter plot -->
<!--            <div>
                <img src="charts/{{ what_class }}-clusters_with_avg_points.png" alt="{{ what_class }} Skill Clusters Scatter Plot">
            </div>
 -->
           <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>

            <div class="footer">
            <p>PoD class data current as of {{ timeStamp }}</p>
            </div>   
        



<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}


//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}


document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});

document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});

document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>





    </body>
    </html>
    """

    def analyze_mercenaries(characters):
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        for char_data in characters:
            if not isinstance(char_data, dict):
                print(f"Skipping unexpected data format: {char_data}")
                continue  # Skip invalid entries

            mercenary = char_data.get("MercenaryType")
            if mercenary:
                readable_mercenary, _ = map_readable_names(mercenary, "")
                mercenary_counts[readable_mercenary] += 1

                for item in char_data.get("MercenaryEquipped", []):
                    worn_category = item.get("Worn", "Unknown")
                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                    title = item.get("Title", "Unknown")
                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1

        return mercenary, mercenary_counts, mercenary_equipment

    # Assuming df is your DataFrame and skill_columns contains the column names for the skills

    # Calculate the total usage of each skill across all clusters
    total_skill_usage = df[skill_columns].sum()

    # Sort skills by total usage in descending order
    most_used_skills = total_skill_usage.sort_values(ascending=False)

    # Sort skills by total usage in ascending order
    least_used_skills = total_skill_usage.sort_values(ascending=True)

    # Extract the top 5 most used skills
    top_5_most_used_skills = most_used_skills.head(5)

    # Extract the bottom 5 least used skills
    bottom_5_least_used_skills = least_used_skills.head(5)


    # Calculate the percentage of characters that have invested in each skill within the cluster
    skill_percentages = df[skill_columns].astype(bool).groupby(df['Cluster']).mean() * 100

    # Identify the top skills per cluster with their average points and percentages
    top_skills_with_avg_and_percent = skill_averages.apply(lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

    summary_label = ""
    summaries = []
    data_folder = "sc/ladder-all"
    # Generate the cluster labels
    cluster_labels = {cluster: f"{cluster} users favor the skills: " + ", ".join([f"{skill} ({avg}%)" for skill, avg in skills]) for cluster, skills in top_skills_with_avg.items()}
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # Combine summaries into a single string
    summary_label = "<br>".join(df['Cluster_Label'].unique())

    # Gather data for the report
    clusters = {}
    for cluster, group in df.groupby('Cluster'):
        sorted_group = group.sort_values(by='Level', ascending=False)  # Sort by level descending
        character_count = len(sorted_group)
        cluster_percentage = cluster_counts[cluster]
        equipment_counts = {}
        for row in sorted_group.itertuples():
            equipment_list = row.Equipment.split(", ")
            for item in equipment_list:
                if item:
                    worn, title_count = item.split(": ", 1)
                    
                    # ✅ Ensure " x1" or any count is always removed
                    if " x" in title_count:
                        title = title_count.rsplit(" x", 1)[0]  # ✅ Use rsplit to remove only the last " xN"
                    else:
                        title = title_count

                    count = int(title_count.split(" x")[-1]) if " x" in title_count else 1

                    if worn not in equipment_counts:
                        equipment_counts[worn] = {}

                    if title in equipment_counts[worn]:
                        equipment_counts[worn][title] += count
                    else:
                        equipment_counts[worn][title] = count  # Initialize with real count

            character_equipment = ", ".join([
                worn + ": " + title.rsplit(" x", 1)[0]  # ✅ Always remove the last " xN"
                for worn, titles in equipment_counts.items()
                for title in titles.keys()
            ])
    

        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)

        # Generate HTML report for mercenaries in this cluster
        merc_count = f"<h3>Mercenary Equipment Analysis for Cluster {cluster}</h3>"

        # Mercenary type counts
        merc_count += "<h4>Count of Mercenary Types</h4>"
        for mercenary, count in mercenary_counts.items():
            merc_count += f"<p>{mercenary}: {count}</p>"

        # Mercenary equipment titles
        merc_count += "<h4>Equipment Titles</h4>"
        for mercenary, equipment in mercenary_equipment.items():
            merc_count += f"<p><strong>{mercenary}:</strong></p>"
            for title, count in equipment.items():
                merc_count += f"<p>{title}: {count}</p>"

        # ✅ Fix: Ensure the cluster exists before adding merc_count
        if cluster not in clusters:
            clusters[cluster] = {}

        if 'merc_count' not in clusters[cluster]:
            clusters[cluster]['merc_count'] = merc_count


        # Calculate total counts for each category
        total_counts = {
            worn: sum(titles.values())
            for worn, titles in equipment_counts.items()
        }

        # Calculate the percentages based on total counts
        equipment_percentages = {
            worn: {title: (count / total_counts[worn]) * 100 for title, count in titles.items()}
            for worn, titles in equipment_counts.items()
        }

        # Get top equipment based on count
        top_equipment = {
            worn: sorted(titles.items(), key=lambda item: item[1], reverse=True)[:5]
            for worn, titles in equipment_counts.items()
        }

        top_equipment_str_list = []
        for worn, titles in top_equipment.items():
            titles_str = "<br>".join([
                f"{title} {percent:.2f}%"  # ✅ Title is already colored
                for title, percent in titles
            ])
            top_equipment_str_list.append(f"<strong>{worn.capitalize()}</strong>: <br>{titles_str}")
        top_equipment_str = "<br>".join(top_equipment_str_list)

        # Use sorted_equipment_counts for full display
        sorted_equipment_counts = {
            worn: dict(sorted(titles.items(), key=lambda item: item[1], reverse=True))
            for worn, titles in equipment_counts.items()
        }

        equipment_counts_str_list = []
        for worn, titles in sorted_equipment_counts.items():
            titles_str = ", ".join([f"{title} {equipment_percentages[worn][title]:.2f}%" for title in titles])
            equipment_counts_str_list.append(f"<strong>{worn.capitalize()}</strong>: {titles_str}")

        equipment_counts_str = "<br>".join(equipment_counts_str_list)


        # Define a helper function to format numbers
        def format_number(num):
            return int(num) if num % 1 == 0 else round(num, 2)

        # Filter top skills
        top_skills = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]

        # Filter other skills, ignoring those with zero points
        other_skills = skill_averages.loc[cluster].drop(top_skills)
        other_skills = other_skills[other_skills > 0].nlargest(6)
        other_skills_pie = "<br>".join([f"{skill} ({format_number(avg)})" for skill, avg in other_skills.items()])
#        other_skills_str = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(other_skills[skill] * character_count)})" for skill in other_skills.index])
        other_skills_str = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(other_skills[skill] * character_count)})</span>"
            for skill in other_skills.index
        ])

        # Filter remaining skills, ignoring those with zero points
        remaining_skills = skill_averages.loc[cluster].sort_values(ascending=False)
        remaining_skills = remaining_skills[remaining_skills > 0]
#        remaining_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str2 = "<br>".join([
            f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
            f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
            f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
            f"({format_number(remaining_skills[skill] * character_count)})</span>"
            for skill in remaining_skills.index
        ])
#        remaining_skills_str_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
        remaining_skills_str_with_icons = "\n".join([
            "<div class='skills-group'>" + "\n".join([
                "<div class='skills-row'>" +
                "\n".join([
                    f"<div class='skill-item'>"
                    f"<div class='skillbar-container'>"
                    f"<div class='skill-info'>"
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                    f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})"
                    f"</div>"
                    f"<div class='skill-mini-bar' style='width: {round(skill_percentages.loc[cluster, skill], 2) * 4}px;'></div>"
                    f"</div>"
                    f"</div>"
                    for skill in remaining_skills.index[row:row+2]
                ]) +
                "</div>"  # Close row
                for row in range(i, min(i+10, len(remaining_skills.index)), 2)
            ]) + "</div>"  # Close group
            for i in range(0, len(remaining_skills.index), 10)
        ])
    #    all_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
    #    all_skills_str2_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
#        sorted_summary_label = ""
#        summary_labels = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]
#        summary = f"{cluster_percentage:.2f}% of {what_class}'s invest heavily in " + ", ".join(summary_labels)
#        summaries.append((cluster_percentage, summary))

        # Generate summaries for each unique Cluster_Label
        unique_cluster_labels = df['Cluster_Label'].unique()

        summaries = []
        data_folder = "sc/ladder-all"
        for cluster_label in unique_cluster_labels:
            # Get the rows corresponding to the current cluster label
            cluster_data = df[df['Cluster_Label'] == cluster_label]
            
            # Extract summary labels (e.g., top skills or other details you want to include)
            summary_labels = cluster_data['Skills'].unique()  # Adjust this based on what summary_labels should contain
            
            # Create summary string
            summary = f"{cluster_label} favor the skills " + ", ".join(summary_labels)
            summaries.append(summary)

        # Output results (example: print summaries)
#        for summary in summaries:
#            print(summary)

        clusters[cluster] = { 
    #        'label': f"{cluster_percentage:.2f}% of {what_class}'s: <br>" + "<br>".join([f"{skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
#            'label': f"{cluster} make up {cluster_percentage:.2f}% of Dual Offensive Aura Granting Items in use <br>Most popular skills used by characters with them equipped:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
#            'label': f"<span style='color:white;'>{cluster} make up {cluster_percentage:.2f}% of Dual Offensive Aura Granting Items in use <br>Most popular skills used by characters with them equipped:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
            'label': f"{cluster_percentage:.2f}% of users with two or more Aura items use {cluster}:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar">
                                <span class="skill-label">{skill} ({int(avg * character_count)})</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
                for skill, avg, percent in top_skills_with_avg_and_percent[cluster]
            ]),
            'character_count': character_count,
            'other_skills': other_skills_str,
            'other_skills_pie': other_skills_pie,
            'characters': [{'name': row.Name, 'level': row.Level, 'skills': row.Skills, 'equipment': row.Equipment, 'mercenary': row.Mercenary, 'mercenary_equipment': row.MercenaryEquipment, 'class': row.Class } for row in sorted_group.itertuples()],
            'top_equipment': top_equipment_str,  # Add top equipment to the data
            'equipment_counts': equipment_counts_str,
            'remaining_skills_with_icons': remaining_skills_str_with_icons,
            'remaining_skills_str2': remaining_skills_str2,  # Add remaining skills string for display without icons
    #        'all_skills_str2': all_skills_str2,
    #        'all_skills_str2_with_icons' : all_skills_str2_with_icons
            'top_5_most_used_skills': top_5_most_used_skills,
            'bottom_5_least_used_skills': bottom_5_least_used_skills,
            'summary_label' : summary_label, 
            'Cluster_labels' : cluster_labels,            
            'mercenary': mercenary,  # Store mercenary type
            'mercenary_equipment': mercenary_equipment,  # Store mercenary's items
#            'filtered_file_count': filtered_file_count,
            
        }
        mercenary, mercenary_counts, mercenary_equipment = analyze_mercenaries(filtered_characters)


    # Ensure the correct percentage values are used
    pie_data = df.groupby('Cluster').agg({
        'Percentage': 'mean',  # Get the mean percentage for each cluster
        'Cluster_Label': 'first'  # Use the first cluster label as representative
    }).reset_index()

    # Include other_skills in customdata
#    pie_data['other_skills_pie'] = pie_data['Cluster'].map(lambda cluster: clusters[cluster]['other_skills_pie'])

    # Combine cluster label and percentage for the pie chart labels
    pie_data['Cluster_Label_Percentage'] = pie_data.apply(lambda row: f"{row['Percentage']:.2f}% ({clusters[row['Cluster']]['character_count']}) - {row['Cluster']}", axis=1)

    # Create a pie chart
    fig_pie = px.pie(
        pie_data,
        values='Percentage',  # Use the correct percentage values
        names='Cluster_Label_Percentage',
        title=f"Offensive Aura Items",
        hover_data={'Cluster_Label': True} #, 'other_skills_pie': True}
    )

    # Update customdata to pass Cluster_Label
    fig_pie.update_traces(customdata=pie_data[['Cluster_Label']]) #, 'other_skills_pie']])

    # Customize the hover template for the pie chart
    fig_pie.update_traces(
        textinfo='percent',  # Keep percentages on the pie slices
        textposition='inside',  # Position percentages inside the pie slices
        hovertemplate="<b>%{customdata[0]}</b><br>Other Skills and Average Point Investment:<br>%{customdata[1]}<extra></extra>",
        marker=dict(line=dict(color='black', width=1)),  # Add a slight outline for clarity
        pull=[0.05] * len(pie_data),  # Slightly pull slices apart to increase visibility
        hole=0  # Ensure it's a full pie (not a donut)
    )

    # Position the legend outside the pie chart and adjust the pie chart size
    fig_pie.update_layout(
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",
            y=-0.15,  # Move it closer
            xanchor="center",
            x=0.5,  # Keep it centered
            font=dict(size=10, color='white'),
            bgcolor='rgba(0,0,0,0)',
#                font=dict(color='white'),  # ✅ Transparent background
        ),
        paper_bgcolor='rgba(0,0,0,0)', # ✅ Transparent background
        margin=dict(l=10, r=10, t=50, b=20),  # Reduce bottom margin to make more space
        width=900,  # Set the width of the entire chart
        height=600,  # Set the height of the entire chart
        font=dict(color='white'),  # ✅ Makes all text white
        title=dict(font=dict(color='white')),  # ✅ Ensures title is also white
#            legend=dict(font=dict(color='white'))  # ✅ Ensures legend text is white
    )

    # Save the pie chart as a PNG file
    fig_pie.write_image(f"pod-stats/charts/{what_class}-clusters_distribution_pie.png")


    # Sort clusters by percentage in descending order
    sorted_clusters = dict(sorted(clusters.items(), key=lambda item: item[1]['character_count'], reverse=True))


    # Ensure the cluster exists before adding merc_count
    if cluster not in clusters:
        clusters[cluster] = {}

    clusters[cluster]['merc_count'] = merc_count

#    print(f"✅ Added merc data for cluster {cluster}:")
#    print(merc_count)

    dt = datetime.now()
    # format it to a string
    timeStamp = dt.strftime('%Y-%m-%d %H:%M')

    # Render the HTML report
    template = Template(html_template)
    html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, timeStamp=timeStamp)  # Pass sorted clusters to the template

    # Save the report to a file
    output_file = f"pod-stats/{what_class}.html"
    with open(output_file, "w") as file:
        file.write(html_content)

    print(f"Cluster analysis report saved to {output_file}")

#GetOffensiveAuraItemsEquipped()



###############################################################
#
# Generate class html's
#
def MakeClassPages():
    # ✅ Class configurations (previously used for folder paths)
    classes = [
        {"what_class": "Barbarian", "howmany_clusters": 14, "howmany_skills": 5},
        {"what_class": "Druid", "howmany_clusters": 14, "howmany_skills": 5},
        {"what_class": "Amazon", "howmany_clusters": 14, "howmany_skills": 5},
        {"what_class": "Assassin", "howmany_clusters": 14, "howmany_skills": 5},
        {"what_class": "Necromancer", "howmany_clusters": 14, "howmany_skills": 5},
        {"what_class": "Paladin", "howmany_clusters": 14, "howmany_skills": 5},
        {"what_class": "Sorceress", "howmany_clusters": 14, "howmany_skills": 5}
    ]

    icons_folder = "icons"

    # ✅ Load the single JSON file
    with open("sc_ladder.json", "r") as file:
        all_characters = json.load(file)

    def map_readable_names(mercenary_type, worn_category=""):
        mercenary_mapping = {
            "Desert Mercenary": "Act 2 Desert Mercenary",
            "Rogue Scout": "Act 1 Rogue Scout",
            "Eastern Sorceror": "Act 3 Eastern Sorceror",
            "Barbarian": "Act 5 Barbarian"
        }
        worn_mapping = {
            "body": "Armor",
            "helmet": "Helmet",
            "weapon1": "Weapon",
            "weapon2": "Offhand"
        }
        readable_mercenary = mercenary_mapping.get(mercenary_type, mercenary_type)
        readable_worn = worn_mapping.get(worn_category, worn_category)
        return readable_mercenary, readable_worn

    def generate_report(what_class, howmany_clusters, howmany_skills, all_characters):
        # ✅ Filter characters by class
        filtered_characters = [char for char in all_characters if char.get("Class") == what_class]

        # ✅ Process Data
        def load_data(filtered_characters):
            all_data = []
            quality_colors = {
                "q_runeword": "#edcd74",
                "q_unique": "#edcd74",
                "q_set": "#45a823",
                "q_magic": "#7074c9",
                "q_rare": "yellow",
                "q_crafted": "orange"
            }

            for char_data in filtered_characters:
                if "SkillTabs" in char_data and "Equipped" in char_data:
                    skill_data = {
                        "Name": char_data.get("Name", "Unknown"),
                        "Class": char_data.get("Class", "Unknown"),
                        "Level": char_data.get("Stats", {}).get("Level", "Unknown")
                    }

                    # ✅ Extract and sort skills
                    skills = []
                    for tab in char_data.get('SkillTabs', []):
                        for skill in tab.get('Skills', []):
                            skill_name = skill['Name']
                            skill_level = skill['Level']
                            skill_data[skill_name] = skill_level
                            skills.append((skill_name, skill_level))

                    skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                    skill_data["Skills"] = ", ".join([
                        f"<img src='{icons_folder}/{name}.png' alt='{name}' class='skill-icon-smaller'> {name}:{level}"
                        for name, level in skills_sorted
                    ])

                    # ✅ Process Equipment
                    equipment_titles = defaultdict(Counter)
                    for item in char_data["Equipped"]:
                        worn_category = item.get("Worn", "Unknown")
                        title = item.get("Title", "Unknown")
                        quality_code = item.get("QualityCode", "default")
                        tag = item.get("Tag", "")

                        # ✅ Standardize worn category names
                        worn_category = {
                            "ring1": "Ring", "ring2": "Ring",
                            "sweapon1": "Left hand", "weapon1": "Left hand",
                            "sweapon2": "Offhand", "weapon2": "Offhand",
                            "body": "Armor", "gloves": "Gloves",
                            "belt": "Belt", "helmet": "Helmet",
                            "boots": "Boots", "amulet": "Amulet"
                        }.get(worn_category, worn_category)

                        # ✅ Set colored title
                        color = quality_colors.get(quality_code, "white")
                        if quality_code in ["q_magic", "q_rare", "q_crafted"]:
                            formatted_tag = f" {tag}" if tag else ""
                            colored_title = f"<span style='color: {color};'>{quality_code.split('_')[1].capitalize()}{formatted_tag}</span>"
                        else:
                            colored_title = f"<span style='color: {color};'>{title}</span>"

                        equipment_titles[worn_category][colored_title] += 1

                    # ✅ Convert equipment data to a readable string
                    skill_data["Equipment"] = ", ".join([
                        f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                        for worn, titles in equipment_titles.items()
                        for title, count in titles.items()
                    ])

                    # ✅ Process mercenary info
                    mercenary_type = char_data.get("MercenaryType", "No mercenary")
                    readable_mercenary, _ = map_readable_names(mercenary_type)
                    mercenary_equipment = ", ".join(
                        [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                    ) if char_data.get("MercenaryEquipped") else "No equipment"

                    skill_data["Mercenary"] = readable_mercenary
                    skill_data["MercenaryEquipment"] = mercenary_equipment

                    all_data.append(skill_data)

            return pd.DataFrame(all_data).fillna(0)  # ✅ Fill missing skills with 0

        # ✅ Load the data
        df = load_data(filtered_characters)

        # Define skill columns (exclude non-skill columns)
        skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment']]

        # Perform PCA
        pca = PCA(n_components=2)
        reduced_data = pca.fit_transform(df[skill_columns])

        # Perform KMeans clustering
#        from sklearn.preprocessing import MinMaxScaler
#        scaler = MinMaxScaler()
#        df[skill_columns] = scaler.fit_transform(df[skill_columns])
#        df['Cluster'] = scaler(df[skill_columns])

        kmeans = KMeans(n_clusters=howmany_clusters, max_iter=500, random_state=42)
        df['Cluster'] = kmeans.fit_predict(df[skill_columns])

#        kmeans = KMeans(n_clusters=howmany_clusters, max_iter=500, init='k-means++', random_state=42)
#        df['Cluster'] = kmeans.fit_predict(df[skill_columns])

#        import matplotlib.pyplot as plt
#        from sklearn.cluster import KMeans

        # Try multiple k values
#        inertia = []
#        k_range = range(2, 15)  # Test different k values

#        for k in k_range:
#            kmeans = KMeans(n_clusters=k, init='k-means++', random_state=42)
#            kmeans.fit(df[skill_columns])
#            inertia.append(kmeans.inertia_)  # Inertia = Sum of squared distances to cluster centers

        # Plot the elbow curve
#        plt.figure(figsize=(8, 5))
#        plt.plot(k_range, inertia, marker='o')
#        plt.xlabel("Number of Clusters (k)")
#        plt.ylabel("Inertia (Within-Cluster Sum of Squares)")
#        plt.title("Elbow Method for Optimal k")
#        plt.show()


        # Calculate the average points invested in skills per cluster
        df['Total_Points'] = df[skill_columns].sum(axis=1)
        cluster_averages = df.groupby('Cluster')['Total_Points'].mean().reset_index()
        cluster_averages.columns = ['Cluster', 'Avg_Points']

        # Merge the averages back into the main DataFrame
        df = pd.merge(df, cluster_averages, on='Cluster')

        # Get skill averages per cluster
        skill_averages = df.groupby('Cluster')[skill_columns].mean()

        # Identify the top skills per cluster with their average points
        top_skills_with_avg = skill_averages.apply(lambda x: [(skill, round(x[skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)

        # Calculate the correct percentages for each cluster
        cluster_counts = df['Cluster'].value_counts(normalize=True) * 100
        df['Percentage'] = df['Cluster'].map(cluster_counts)

        # Map clusters to meaningful names (top skills with average points)
        cluster_labels = {i: ", ".join([f"{skill} ({avg})" for skill, avg in skills]) for i, skills in enumerate(top_skills_with_avg)}
        df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

        # Counters for classes, runewords, uniques, and set items
        class_counts = {}
        runeword_counter = Counter()
        unique_counter = Counter()
        set_counter = Counter()
        synth_counter = Counter()
        crafted_counters = {
            "Rings": Counter(),
            "Weapons and Shields": Counter(),
            "Arrows": Counter(),
            "Bolts": Counter(),
            "Body Armor": Counter(),
            "Gloves": Counter(),
            "Belts": Counter(),
            "Helmets": Counter(),
            "Boots": Counter(),
            "Amulets": Counter(),
        }
        magic_counters = {
            "Rings": Counter(),
            "Weapons and Shields": Counter(),
            "Arrows": Counter(),
            "Bolts": Counter(),
            "Body Armor": Counter(),
            "Gloves": Counter(),
            "Belts": Counter(),
            "Helmets": Counter(),
            "Boots": Counter(),
            "Amulets": Counter(),
        }
        rare_counters = {
            "Rings": Counter(),
            "Weapons and Shields": Counter(),
            "Arrows": Counter(),
            "Bolts": Counter(),
            "Body Armor": Counter(),
            "Gloves": Counter(),
            "Belts": Counter(),
            "Helmets": Counter(),
            "Boots": Counter(),
            "Amulets": Counter(),
        }
        
        synth_sources = {}  # Maps item names to all synth items that used them

        runeword_users = {}
        unique_users = {}
        set_users = {}
        synth_users = {}
        crafted_users = {category: {} for category in crafted_counters}  # Ensure all categories exist
        rare_users = {category: {} for category in crafted_counters}  # Ensure all categories exist
        magic_users = {category: {} for category in crafted_counters}  # Ensure all categories exist

        all_characters = []
        sorted_just_socketed_runes = {}
        sorted_just_socketed_excluding_runewords_runes = {}
        all_other_items = {}

        def process_all_characters(filtered_characters):
            """Processes all characters from the single JSON file instead of iterating through folders."""

            # Dictionary to store class counts
            class_counts = Counter()

            # Counters for different item types
            runeword_counter = Counter()
            unique_counter = Counter()
            set_counter = Counter()
            synth_counter = Counter()
            crafted_counters = defaultdict(Counter)

            # User tracking dictionaries
            runeword_users = defaultdict(list)
            unique_users = defaultdict(list)
            set_users = defaultdict(list)
            synth_users = defaultdict(list)
            crafted_users = defaultdict(lambda: defaultdict(list))
#            synth_sources = defaultdict(list)

            def categorize_worn_slot(worn_category, text_tag):
                if worn_category in ["sweapon1", "weapon1", "sweapon2", "weapon2"]:
                    if text_tag == "Arrows":
                        return "Arrows"
                    elif text_tag == "Bolts":
                        return "Bolts"
                    else:
                        return "Weapons and Shields"

                worn_category_map = {
                    "ring1": "Ring", "ring2": "Ring",
                    "body": "Armor",
                    "gloves": "Gloves",
                    "belt": "Belt",
                    "helmet": "Helmet",
                    "boots": "Boots",
                    "amulet": "Amulets",
                }

                return worn_category_map.get(worn_category, "Other")  # Default to "Other"

            # ✅ Iterate through all characters in the JSON file
            for char_data in filtered_characters:
                char_name = char_data.get("Name", "Unknown")
                char_class = char_data.get("Class", "Unknown")
                char_level = char_data.get("Stats", {}).get("Level", "Unknown")

                # ✅ Count classes
                class_counts[char_class] += 1

                # ✅ Process equipped items
                for item in char_data.get("Equipped", []):
                    worn_category = categorize_worn_slot(item.get("Worn", ""), item.get("TextTag", ""))
                    character_info = {"name": char_name, "class": char_class, "level": char_level}

                    # ✅ Process Synthesized items
                    if "synth" in item.get("Tag", "").lower() or "synth" in item.get("TextTag", "").lower():
                        item_title = item["Title"]
                        synth_counter[item_title] += 1
                        synth_users.setdefault(item_title, []).append(character_info)

                        # Process SynthesisedFrom property
                        synthesized_from = item.get("SynthesisedFrom", [])
                        all_related_items = [item_title] + synthesized_from
                        for source_item in all_related_items:
#                            print(f"{source_item}")
                            synth_sources.setdefault(source_item, []).append({
                                "name": char_name,
                                "class": char_class,
                                "level": char_level,
                                "synthesized_item": item_title
                            })
#                        print(f"{synth_sources}")

                    # ✅ Process item qualities
                    quality_code = item.get("QualityCode", "")
                    if quality_code == "q_runeword":
                        runeword_counter[item["Title"]] += 1
                        runeword_users[item["Title"]].append(character_info)

                    elif quality_code == "q_unique":
                        unique_counter[item["Title"]] += 1
                        unique_users[item["Title"]].append(character_info)

                    elif quality_code == "q_set":
                        set_counter[item["Title"]] += 1
                        set_users[item["Title"]].append(character_info)

                    elif quality_code == "q_crafted":
                        crafted_counters[worn_category][item["Title"]] += 1
                        crafted_users[worn_category][item["Title"]].append(character_info)

            return (
                class_counts, runeword_counter, unique_counter, set_counter, synth_counter,
                runeword_users, unique_users, set_users, synth_users, crafted_counters, crafted_users
            )

        def process_all_characters_for_magic_rare(filtered_characters):
            """Processes all characters for magic and rare items using the single JSON file."""

            magic_counters = defaultdict(Counter)
            rare_counters = defaultdict(Counter)
            magic_users = defaultdict(lambda: defaultdict(list))
            rare_users = defaultdict(lambda: defaultdict(list))

            def categorize_worn_slot(worn_category, text_tag):
                if worn_category in ["sweapon1", "weapon1", "sweapon2", "weapon2"]:
                    if text_tag == "Arrows":
                        return "Arrows"
                    elif text_tag == "Bolts":
                        return "Bolts"
                    else:
                        return "Weapons and Shields"

                worn_category_map = {
                    "ring1": "Ring", "ring2": "Rings",
                    "body": "Armor",
                    "gloves": "Gloves",
                    "belt": "Belts",
                    "helmet": "Helmets",
                    "boots": "Boots",
                    "amulet": "Amulets",
                }

                return worn_category_map.get(worn_category, "Other")  # Default to "Other"

            # ✅ Iterate through all characters
            for char_data in filtered_characters:
                char_name = char_data.get("Name", "Unknown")
                char_class = char_data.get("Class", "Unknown")
                char_level = char_data.get("Stats", {}).get("Level", "Unknown")

                # ✅ Process equipped items
                for item in char_data.get("Equipped", []):
                    worn_category = categorize_worn_slot(item.get("Worn", ""), item.get("TextTag", ""))
                    character_info = {"name": char_name, "class": char_class, "level": char_level}

                    quality_code = item.get("QualityCode", "")
                    if quality_code == "q_magic":
                        magic_counters[worn_category][item["Title"]] += 1
                        magic_users[worn_category][item["Title"]].append(character_info)

                    elif quality_code == "q_rare":
                        rare_counters[worn_category][item["Title"]] += 1
                        rare_users[worn_category][item["Title"]].append(character_info)

            return magic_counters, magic_users, rare_counters, rare_users

        class_counts, runeword_counter, unique_counter, set_counter, synth_counter, runeword_users, unique_users, set_users, synth_users, crafted_counters, crafted_users = process_all_characters(filtered_characters)

        magic_counters, magic_users, rare_counters, rare_users = process_all_characters_for_magic_rare(filtered_characters)

        # Get the most common items
        most_common_runewords = runeword_counter.most_common(10)
        most_common_uniques = unique_counter.most_common(10)
        most_common_set_items = set_counter.most_common(10)

        # Get all the items
        all_runewords = runeword_counter.most_common(150)
        all_uniques = unique_counter.most_common(150)
        all_set = set_counter.most_common(150)
        all_synth = synth_counter.most_common(150)

        # Get the least common items
        least_common_runewords = runeword_counter.most_common()[:-11:-1]
        least_common_uniques = unique_counter.most_common()[:-11:-1]
        least_common_set_items = set_counter.most_common()[:-11:-1]

        # Generate list items
        def generate_list_items(items):
            return ''.join(f'<li>{item}: {count}</li>' for item, count in items)

        def generate_all_list_items(counter, character_data):
            if not isinstance(character_data, list):
                print("Error: character_data is not a list! Type:", type(character_data))
                return ""  # Return an empty string to avoid breaking HTML generation

            items_html = ""

            for item, count in counter:

                # Handle normal cases
                if counter != synth_counter:
                    character_list = [
                        char
                        for char in character_data
                        if isinstance(char, dict) and any(
                            equipped_item.get("Title") == item for equipped_item in char.get("Equipped", [])
                        )
                    ]
                # Handle synth items separately
                if counter == synth_counter:
                    character_list = [
                        char for char in synth_users.get(item, [])
                        if "synth" in char["item"].get("Tag", "").lower() or "synth" in char["item"].get("TextTag", "").lower()
                    ]
    #            print(f"Processing item: {item}, Expected count: {count}")
    #            print(f"Characters in list: {[char['Name'] for char in character_list]}")
    #                print(f"Synth Users for {item}: {character_list}")
    #            print(f"Synth Users for {item}: {[char['Name'] for char in character_list]}")

                character_list_html = "".join(
                    f""" 
                    <div class="character-info">
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char["Name"]}" target="_blank">
                                {char["Name"]}
                            </a>
                        </div>
                        <div>Level {char["Stats"]["Level"]} {char["Class"]}</div>
                        <div class="hover-trigger" data-character-name="{char["Name"]}"><!-- Armory Quickview--></div>
                    </div>
                    <div class="character">
                        <div class="popup hidden"></div> <!-- No iframe inside initially -->
                    </div>
                    """
                    for char in character_list
                )

                items_html += f"""
                <button class="collapsible">
                    <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                    <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                    <strong>{item} ({count} users)</strong>
                </button>
                <div class="content">
                    {character_list_html if character_list else "<p>No characters using this item.</p>"}
                </div>
                """
#            print(f"Checking synth users for item: {item}")
    #        for char in character_list:
    #            print(f"- {char['name']} (Lvl {char['level']} {char['class']}) - Item: {char['item'].get('Title')}")

            return items_html

        def generate_synth_list_items(counter: Counter, synth_users: dict):
            items_html = ""
    #        for item, count in counter.items():
            for item, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):

                character_list = synth_users.get(item, [])  # Directly fetch correct list

                character_list_html = "".join(
                    f""" 
                    <div class="character-info">
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                                {char["name"]}
                            </a>
                        </div>
                        <div>Level {char["level"]} {char["class"]}</div>
                        <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                    </div>
                    <div class="character">
                        <div class="popup hidden"></div> <!-- No iframe inside initially -->
                    </div>
                    """ for char in character_list
                )

                items_html += f""" 
                <button class="collapsible">
                    <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                    <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                    <strong>{item} ({count} users)</strong>
                </button>
                <div class="content">
                    {character_list_html if character_list else "<p>No characters using this item.</p>"}
                </div>
                """
            
            return items_html

        synth_user_count = sum(len(users) for users in synth_users.values())

        def generate_synth_source_list(synth_sources):
            items_html = ""

    #        for source_item, characters in synth_sources.items():
            for source_item, characters in sorted(synth_sources.items(), key=lambda x: (-len(x[1]), x[0])):
        
                character_list_html = "".join(
                    f"""
                    <div class="character-info">
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                                {char["name"]}
                            </a>
                        </div>
                        <div>Level {char["level"]} {char["class"]}</div>
                        <div>Used in: <strong>{char["synthesized_item"]}</strong></div>
                        <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                    </div>
                    <div class="character">
                        <div class="popup hidden"></div> <!-- No iframe inside initially -->
                    </div>
                    """ for char in characters
                )

                items_html += f"""
                <button class="collapsible">
                    <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                    <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">

                    <strong>{source_item} (Found in {len(characters)} Items)</strong>
                </button>
                <div class="content">
                    {character_list_html if characters else "<p>No synth items used this.</p>"}
                </div>
                """

            return items_html
        synth_source_user_count = sum(len(users) for users in synth_sources.values())


        def generate_crafted_list_items(crafted_counters, crafted_users):
            items_html = ""

            for worn_category, counter in crafted_counters.items():
                if not counter:  # Skip empty categories
                    continue
                
                # Collect all characters in this category
                category_users = []
                for item, count in counter.items():
                    category_users.extend(crafted_users.get(worn_category, {}).get(item, []))

                # Skip categories with no users
                if not category_users:
                    continue

                # Create the list of all users in this category
                character_list_html = "".join(
                    f"""
                    <div class="character-info">
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                                {char["name"]}
                            </a>
                        </div>
                        <div>Level {char["level"]} {char["class"]}</div>
                        <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                    </div>
                    <div class="character">
                        <div class="popup hidden"></div> <!-- No iframe inside initially -->
                    </div>
                    """ for char in category_users
                )

                # Create a collapsible button for each category
                items_html += f"""
                <button class="collapsible">
                    <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                    <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                    <strong>Crafted {worn_category} ({len(category_users)} users)</strong>
                </button>
                <div class="content">
                    {character_list_html if category_users else "<p>No characters using crafted items in this category.</p>"}
                </div>
                """

            return items_html
        craft_user_count = sum(len(users) for users in crafted_users.values())


        def generate_magic_list_items(magic_counters, magic_users):
            items_html = ""

            for worn_category, counter in magic_counters.items():
                if not counter:  # Skip empty categories
                    continue
                
                # Collect all characters in this category
                category_users = []
                for item, count in counter.items():
                    category_users.extend(magic_users.get(worn_category, {}).get(item, []))

                # Skip categories with no users
                if not category_users:
                    continue

                # Create the list of all users in this category
                character_list_html = "".join(
                    f"""
                    <div class="character-info">
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                                {char["name"]}
                            </a>
                        </div>
                        <div>Level {char["level"]} {char["class"]}</div>
                        <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                    </div>
                    <div class="character">
                        <div class="popup hidden"></div> <!-- No iframe inside initially -->
                    </div>
                    """ for char in category_users
                )

                # Create a collapsible button for each category
                items_html += f"""
                <button class="collapsible">
                    <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                    <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                    <strong>Magic {worn_category} ({len(category_users)} users)</strong>
                </button>
                <div class="content">
                    {character_list_html if category_users else "<p>No characters using magic items in this category.</p>"}
                </div>
                """

            return items_html
        magic_user_count = sum(len(users) for users in magic_users.values())


        def generate_rare_list_items(rare_counter, rare_users):
            items_html = ""

            for worn_category, counter in rare_counter.items():
                if not counter:  # Skip empty categories
                    continue
                
                # Collect all characters in this category
                category_users = []
                for item, count in counter.items():
                    category_users.extend(rare_users.get(worn_category, {}).get(item, []))

                # Skip categories with no users
                if not category_users:
                    continue

                # Create the list of all users in this category
                character_list_html = "".join(
                    f"""
                    <div class="character-info">
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                                {char["name"]}
                            </a>
                        </div>
                        <div>Level {char["level"]} {char["class"]}</div>
                        <div class="hover-trigger" data-character-name="{char["name"]}"></div>
                    </div>
                    <div class="character">
                        <div class="popup hidden"></div> <!-- No iframe inside initially -->
                    </div>
                    """ for char in category_users
                )

                # Create a collapsible button for each category
                items_html += f"""
                <button class="collapsible">
                    <img src="icons/open-grey.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                    <img src="icons/closed-grey.png" alt="Runewords Close" class="icon-small close-icon">
                    <strong>Rare {worn_category} ({len(category_users)} users)</strong>
                </button>
                <div class="content">
                    {character_list_html if category_users else "<p>No characters using Rare items in this category.</p>"}
                </div>
                """

            return items_html
        rare_user_count = sum(len(users) for users in rare_users.values())

        def socket_html(filtered_characters):
            """Generates socketed item analysis from sc_ladder.json."""

            rune_names = {
                "El Rune", "Eld Rune", "Tir Rune", "Nef Rune", "Eth Rune", "Ith Rune", "Tal Rune", "Ral Rune", "Ort Rune", "Thul Rune", "Amn Rune", "Sol Rune",
                "Shael Rune", "Dol Rune", "Hel Rune", "Io Rune", "Lum Rune", "Ko Rune", "Fal Rune", "Lem Rune", "Pul Rune", "Um Rune", "Mal Rune", "Ist Rune",
                "Gul Rune", "Vex Rune", "Ohm Rune", "Lo Rune", "Sur Rune", "Ber Rune", "Jah Rune", "Cham Rune", "Zod Rune"
            }

            # ✅ Categorization
            all_items = []
            socketed_items = []
            items_excluding_runewords = []
            just_socketed = []
            just_socketed_excluding_runewords = []
            facet_elements = defaultdict(list)
            shields_for_skulls = []
            weapons_for_skulls = []
            helmets_for_skulls = []
            armor_for_skulls = []
            jewel_counts = Counter()
            jewel_groupings = {"magic": [], "rare": []}

            # ✅ Function to extract Rainbow Facet element type
            def extract_element(item):
                if item.get('Title') == 'Rainbow Facet':
                    element_types = ["fire", "cold", "lightning", "poison", "physical", "magic"]
                    for element in element_types:
                        for prop in item.get('PropertyList', []):
                            if element in prop.lower():
                                return element.capitalize()
                return item.get('Title', 'Unknown')  # Use title if not "Rainbow Facet"

            # ✅ Process all characters
            for char_data in filtered_characters:
                for item in char_data.get('Equipped', []):

                    # ✅ Categorize Perfect Skulls
                    worn_category = item.get('Worn', '')
                    for socketed_item in item.get('Sockets', []):
                        if socketed_item.get('Title') == "Perfect Skull":
                            if worn_category == 'helmet':
                                helmets_for_skulls.append(socketed_item)
                            elif worn_category == 'body':
                                armor_for_skulls.append(socketed_item)
                            elif worn_category in ['weapon1', 'weapon2', 'sweapon1', 'sweapon2']:
                                if any("Block" in prop for prop in item.get('PropertyList', [])):  # ✅ Identify shields
                                    shields_for_skulls.append(socketed_item)
                                else:
                                    weapons_for_skulls.append(socketed_item)

                    # ✅ Process socketed items
                    if item.get('SocketCount', '0') > '0':  # Item has sockets
                        all_items.append(item)
                        if item.get('QualityCode') != 'q_runeword':  # Exclude runewords
                            items_excluding_runewords.append(item)

                        for socketed_item in item.get('Sockets', []):
                            element = extract_element(socketed_item)
                            socketed_items.append(socketed_item)
                            facet_elements[element].append(socketed_item)
                            just_socketed.append(socketed_item)

                            # ✅ Categorize Magic & Rare Jewels
                            quality_code = socketed_item.get('QualityCode', '')
                            if quality_code == "q_magic":
                                socketed_item["GroupedTitle"] = "Misc. Magic Jewels"
                            elif quality_code == "q_rare":
                                socketed_item["GroupedTitle"] = "Misc. Rare Jewels"
                            else:
                                socketed_item["GroupedTitle"] = socketed_item.get("Title", "Unknown")

                            if item.get('QualityCode') != 'q_runeword':
                                just_socketed_excluding_runewords.append(socketed_item)

            # ✅ Function to count socketed items
            def count_items_by_type(items):
                rune_counter = Counter()
                non_rune_counter = Counter()
                magic_jewel_counter = Counter()
                rare_jewel_counter = Counter()
                facet_counter = defaultdict(lambda: {"count": 0, "perfect": 0})

                for item in items:
                    title = item.get('Title', 'Unknown')
                    quality = item.get('QualityCode', '')

                    if title in rune_names:
                        rune_counter[title] += 1
                    elif "Rainbow Facet" in title:
                        element = extract_element(item)
                        facet_counter[element]["count"] += 1
                        properties = item.get('PropertyList', [])
                        if any("+5" in prop for prop in properties) and any("-5" in prop for prop in properties):
                            facet_counter[element]["perfect"] += 1
                    elif quality == "q_magic":
                        has_splash = any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                        has_ias = any("attack speed" in prop.lower() for prop in item.get("PropertyList", []))
                        has_ed = any("enhanced damage" in prop.lower() for prop in item.get("PropertyList", []))
                        has_iassplash = has_ias and has_splash
                        has_iased = has_ias and has_ed
                        magic_jewel_counter["Misc. Magic Jewels"] += 1
                        if has_splash:
                            magic_jewel_counter["splash"] += 1
                        if has_ias:
                            magic_jewel_counter["attack speed"] += 1
                        if has_ed:
                            magic_jewel_counter["enhanced damage"] += 1
                        if has_iassplash:
                            magic_jewel_counter["iassplash"] += 1
                        if has_iased:
                            magic_jewel_counter["iased"] += 1
                    elif quality == "q_rare":
                        has_splash = any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                        has_ed = any("enhanced damage" in prop.lower() for prop in item.get("PropertyList", []))
                        rare_jewel_counter["Misc. Rare Jewels"] += 1
                        if has_splash:
                            rare_jewel_counter["splash"] += 1
                        if has_ed:
                            rare_jewel_counter["enhanced damage"] += 1
                    else:
                        non_rune_counter[title] += 1

                return rune_counter, non_rune_counter, magic_jewel_counter, rare_jewel_counter, facet_counter

            # ✅ Unpacking correctly for all five values
            just_socketed_runes, just_socketed_non_runes, just_socketed_magic, just_socketed_rare, just_socketed_facets = count_items_by_type(just_socketed)
            just_socketed_excluding_runewords_runes, just_socketed_excluding_runewords_non_runes, just_socketed_excluding_runewords_magic, just_socketed_excluding_runewords_rare, just_socketed_excluding_runewords_facets = count_items_by_type(just_socketed_excluding_runewords)

            # ✅ Sort items for output
            sorted_just_socketed_runes = just_socketed_runes.most_common()
            sorted_just_socketed_excluding_runewords_runes = just_socketed_excluding_runewords_runes.most_common()

            # ✅ Combine non-runes, magic, rare, and facets into a single list
            all_other_items = [
                *(f"{item}: {count}" for item, count in just_socketed_excluding_runewords_non_runes.items()),
                f"Misc. Magic Jewels: {just_socketed_excluding_runewords_magic['Misc. Magic Jewels']} "
                f"({just_socketed_excluding_runewords_magic['splash']} Splash, {just_socketed_excluding_runewords_magic['attack speed']} IAS, "
                f"{just_socketed_excluding_runewords_magic['enhanced damage']} ED; {just_socketed_excluding_runewords_magic['iassplash']} IAS/Splash, {just_socketed_excluding_runewords_magic['iased']} IAS/ED)",
                f"Misc. Rare Jewels: {just_socketed_excluding_runewords_rare['Misc. Rare Jewels']} "
                f"({just_socketed_excluding_runewords_rare['splash']} Splash, {just_socketed_excluding_runewords_rare['enhanced damage']} ED)",
                *(f"Rainbow Facet ({element}): {counts['count']} ({counts['perfect']} Perfect)" for element, counts in just_socketed_excluding_runewords_facets.items())
            ]

            return (
                format_socket_html_runes(sorted_just_socketed_runes),
                format_socket_html_runes(sorted_just_socketed_excluding_runewords_runes),
                format_socket_html(all_other_items)
            )

        def format_socket_html(counter_data):
            """Formats socketed items as an HTML table or list."""
            if isinstance(counter_data, list):  # If it's a list, format as an unordered list
                items = "".join(f"<li>{item}</li>" for item in counter_data)
                return f"<ul>{items}</ul>"

            elif isinstance(counter_data, Counter):  # If it's a Counter, format as a table
                rows = "".join(f"<tr><td>{item}</td><td>{count}</td></tr>" for item, count in counter_data.items())
                return f"<table><tr><th>Item</th><th>Count</th></tr>{rows}</table>"

            elif isinstance(counter_data, dict):  # If it's a dict (e.g., facet counts), format as a list
                items = "".join(f"<li>{item}: {count['count']} ({count['perfect']} perfect)</li>" for item, count in counter_data.items())
                return f"<ul>{items}</ul>"

            return ""  # Return empty string if there's no data

        def format_socket_html_runes(counter_data):
            """Formats socketed items as an HTML table or list."""
            if isinstance(counter_data, list):  # If it's a list of tuples (like runes), format properly
                items = "".join(f"<li>{item}: {count}</li>" for item, count in counter_data)
                return f"<ul>{items}</ul>"

            elif isinstance(counter_data, Counter):  # If it's a Counter, format as a table
                rows = "".join(f"<tr><td>{item}</td><td>{count}</td></tr>" for item, count in counter_data.items())
                return f"<table><tr><th>Item</th><th>Count</th></tr>{rows}</table>"

            elif isinstance(counter_data, dict):  # If it's a dict (e.g., facet counts), format as a list
                items = "".join(f"<li>{item}: {count['count']} ({count['perfect']} perfect)</li>" for item, count in counter_data.items())
                return f"<ul>{items}</ul>"

            return ""  # Return empty string if there's no data






        def GetSCFunFacts(filtered_characters):
            """Generates softcore fun facts using sc_ladder.json."""
            
            # ✅ Extract alive characters (not dead)
            alive_characters = [char for char in filtered_characters if not char.get("IsDead", True)]
            undead_count = len(alive_characters)
            character_count = len(filtered_characters)  # Total characters

            # ✅ Function to generate the alive characters list
            def GetTheLiving():
                return "".join(
                    f"""
                    <div class="character-info">
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char.get("Name", "Unknown")}" target="_blank">
                                {char.get("Name", "Unknown")}
                            </a>
                        </div>
                        <div>Level {char.get("Stats", {}).get("Level", "N/A")}</div>
                        <div class="hover-trigger" data-character-name="{char.get("Name", "Unknown")}"></div>
                    </div>
                    <div class="character">
                        <div class="popup hidden"></div> <!-- No iframe inside initially -->
                    </div>
                    """ for char in alive_characters
                )

            alive_list_html = GetTheLiving()

            # ✅ Function to get the top 5 characters for a given stat
            def get_top_characters(stat_name):
                ranked = sorted(
                    filtered_characters,
                    key=lambda c: c.get("Stats", {}).get(stat_name, 0) + c.get("Bonus", {}).get(stat_name, 0),
                    reverse=True,
                )[:5]  # Top 5

                return "".join(
                    f"""<li>&nbsp;&nbsp;&nbsp;&nbsp;
                        <a href="https://pathofdiablo.com/p/armory/?name={char.get('Name', 'Unknown')}" target="_blank">
                            {char.get('Name', 'Unknown')} ({char.get('Stats', {}).get(stat_name, 0) + char.get('Bonus', {}).get(stat_name, 0)})
                        </a>
                    </li>"""
                    for char in ranked
                )

            # ✅ Get the top 5 for each stat
            top_strength = get_top_characters("Strength")
            top_dexterity = get_top_characters("Dexterity")
            top_vitality = get_top_characters("Vitality")
            top_energy = get_top_characters("Energy")
            top_life = get_top_characters("Life")
            top_mana = get_top_characters("Mana")

            # ✅ Compute Magic Find (MF) and Gold Find (GF)
            total_mf = 0
            total_gf = 0
            total_life = 0
            total_mana = 0

            for char in filtered_characters:
                mf = char.get("Bonus", {}).get("MagicFind", 0) + \
                    char.get("Bonus", {}).get("WeaponSetMain", {}).get("MagicFind", 0) + \
                    char.get("Bonus", {}).get("WeaponSetOffhand", {}).get("MagicFind", 0)
                gf = char.get("Bonus", {}).get("GoldFind", 0) + \
                    char.get("Bonus", {}).get("WeaponSetMain", {}).get("GoldFind", 0) + \
                    char.get("Bonus", {}).get("WeaponSetOffhand", {}).get("GoldFind", 0)
                life = char.get("Stats", {}).get("Life", 0)
                mana = char.get("Stats", {}).get("Mana", 0)

                total_mf += mf
                total_gf += gf
                total_life += life
                total_mana += mana

            top_magic_find = get_top_characters("MagicFind")
            top_gold_find = get_top_characters("GoldFind")

            # ✅ Calculate averages
            average_mf = total_mf / character_count if character_count > 0 else 0
            average_gf = total_gf / character_count if character_count > 0 else 0
            average_life = total_life / character_count if character_count > 0 else 0
            average_mana = total_mana / character_count if character_count > 0 else 0

            # ✅ Generate fun facts HTML
            fun_facts_html = f"""
            <h3>Softcore Fun Facts</h3>
                <h3>{undead_count} {what_class}'s out of {character_count} have not died</h3>
                    <button type="button" class="collapsible sets-button">
                        <img src="icons/Special_click.png" alt="Undead Open" class="icon open-icon hidden">
                        <img src="icons/Special.png" alt="Undead Close" class="icon close-icon">
                    </button>
                    <div class="content">  
                        <div id="special">{alive_list_html}</div>
                    </div>
            <br>

            <!-- Strength & Dexterity Row -->
            <div class="fun-facts-row">
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Strength:</h3>
                    <ul>{top_strength}</ul>
                </div>
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Dexterity:</h3>
                    <ul>{top_dexterity}</ul>
                </div>
            </div>

            <!-- Vitality & Energy Row -->
            <div class="fun-facts-row">
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Vitality:</h3>
                    <ul>{top_vitality}</ul>
                </div>
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Energy:</h3>
                    <ul>{top_energy}</ul>
                </div>
            </div>

            <!-- Life & Mana Row -->
            <div class="fun-facts-row">
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Life:</h3>
                    <ul>{top_life}</ul>
                    <p><strong>Average Life:</strong> {average_life:.2f}</p>
                </div>
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Mana:</h3>
                    <ul>{top_mana}</ul>
                    <p><strong>Average Mana:</strong> {average_mana:.2f}</p>
                </div>
            </div>

            <!-- Magic Find & Gold Find Row -->
            <div class="fun-facts-row">
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Magic Find:</h3>
                    <ul>{top_magic_find}</ul>
                    <p><strong>Average Magic Find:</strong> {average_mf:.2f}</p>
                </div>
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the Most Gold Find:</h3>
                    <ul>{top_gold_find}</ul>
                    <p><strong>Average Gold Find:</strong> {average_gf:.2f}</p>
                </div>
            </div>
            """

            return fun_facts_html

        # Load the consolidated JSON
        with open("sc_ladder.json", "r") as file:
            all_characters = json.load(file)

        fun_facts_html = GetSCFunFacts(filtered_characters)


        # Updated HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ what_class }} Analysis Report</title>

        </head>
        <body class="main special-background-{{ what_class|lower }}">
    
        <div class="hamburger" onclick="toggleMenu()">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
        </div>
        <div class="top-buttons">
            <a href="Home.html" class="top-button home-button" onclick="setActive('Home')"></a>
            <a href="#" id="SC_HC" class="top-button"> </a>
            <a href="Amazon.html" id="Amazon" class="top-button amazon-button"></a>
            <a href="Assassin.html" id="Assassin" class="top-button assassin-button"></a>
            <a href="Barbarian.html" id="Barbarian" class="top-button barbarian-button"></a>
            <a href="Druid.html" id="Druid" class="top-button druid-button"></a>
            <a href="Necromancer.html" id="Necromancer" class="top-button necromancer-button"></a>
            <a href="Paladin.html" id="Paladin" class="top-button paladin-button"></a>
            <a href="Sorceress.html" id="Sorceress" class="top-button sorceress-button"></a>
            <a href="https://github.com/qordwasalreadytaken/pod-stats/blob/main/README.md" class="top-button about-button" target="_blank"></a>
        </div>
<div page-intro-class>
            <h1>{{ what_class }} Softcore Skill Distribution </h1>
            <div class="summary-container">

            <p class="indented-skills"> </p>


<!--        <h2>Detailed Grouping Information, Ordered Highest to Lowest %</h2>-->

        {% for clusters, data in clusters.items() %}
        <!--<h2>{{ data['label'] }}</h2>
        <p class="indented-skills"><strong>Other Skills:<br></strong> {{ data['other_skills'] }}</p> -->
        <div class="class-intro">
        <div id="skills" class="skills-container">
            <div class="column">
                <ul id="most-popular-skills">
                    <h2>{{ data['label'] }}</h2>
                </ul>
            </div>
<!--            <div class="column">
                <ul id="other-skills">
                    <h2>Other common skills in this group:</h2> {{ data['other_skills'] }}
                </ul>
            </div> -->
        </div>

    <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>All Skills</strong></button>
                <div class="content">
                    <div>{{ data['remaining_skills_with_icons'] }}</div>
                </div>

                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>Most Common Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['top_equipment'] }}</div>
                </div>
<!--            
                <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
                <strong>ALL Equipment:</strong></button>
                <div class="content">
                    <div>{{ data['equipment_counts'] }}</div>
                </div>
-->
            <button type="button" class="collapsible small-collapsible">
        <img src="icons/open.png" alt="Open" class="icon-small open-icon hidden">
        <img src="icons/closed.png" alt="Close" class="icon-small close-icon">
            <strong>{{ data['character_count'] }} Characters in this cluster:</strong>
        </button>
        <div class="content">
{% for character in data['characters'] %}
<!--
<div class="character-container {% if loop.index is even %}char1{% else %}char2{% endif %}">
-->
<div class="character-container char2">
    <div class="character-info">
        <div class="character-link"><strong>Name: <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}
            </a></strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div class="hover-trigger" data-character-name="{{ character['name'] }}">
            <!-- Armory Quickview -->
        </div>
    </div>

    <div class="character">
        <div class="popup hidden"></div> <!-- No iframe inside initially -->
    </div>

    <p><strong>Skills:<br></strong> {{ character['skills'] }}</p>
    <p><strong>Equipment:<br></strong> {{ character['equipment'] }}</p>
    <p><strong>Mercenary:<br></strong> {{ character['mercenary'] }} - {{ character['mercenary_equipment'] }}</p>

    <div class="character-section" data-character-name="{{ character['name'] }}"></div>
</div>
<hr color="#141414">
<br>
{% endfor %}
            <br>
            </div>
            </div>
        <!--    <hr width="90%"> -->
            <br>
            {% endfor %}
                <h3>Top 5 Most Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in top_5_most_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>

            <h3>Bottom 5 Least Popular {{ what_class }} Skills:</h3>
            <ul>
                {% for skill, usage in bottom_5_least_used_skills.items() %}
                <li>{{ skill }}: {{ usage }}</li>
                {% endfor %}
            </ul>
            <br>
            <hr>
            <br>
                            {{ full_summary_output }}
            <br>
            </div>
            </div>
            <br><br>
                    <!-- Embed the Plotly pie chart -->
            <div>
                <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
            </div> 
            <hr>
            <h1>Equipment and item details for {{ what_class}}</h1>
            <button type="button" class="collapsible runewords-button">
                <img src="icons/Runewords_click.png" alt="Runewords Open" class="icon open-icon hidden">
                <img src="icons/Runewords.png" alt="Runewords Close" class="icon close-icon">
            <!--    <strong>Runewords</strong> -->
            </button>
            <div class="content">
                <div id="runewords" class="container">
                    <div class="column">
                        <h3>Most Used Runewords:</h3>
                        <ul id="most-popular-runewords">
                            {most_popular_runewords}
                        </ul>
                    </div>
                    <div class="column">
                        <h3>Least Used Runewords:</h3>
                        <ul id="least-popular-runewords">
                            {least_popular_runewords}
                        </ul>
                    </div>
                </div>


                <button type="button" class="collapsible small-collapsible">
                    <img src="icons/open.png" alt="All Runewords Open" class="icon-small open-icon hidden">
                    <img src="icons/closed.png" alt="Runewords Close" class="icon-small close-icon">
                    <strong>ALL Runewords</strong>
                </button>

                <div class="content">
                    <div id="allrunewords">
                        {all_runewords}
                    </div>
                </div>
            </div>

            <br>
            <button type="button" class="collapsible uniques-button">
                <img src="icons/Uniques_click.png" alt="Uniques Open" class="icon open-icon hidden">
                <img src="icons/Uniques.png" alt="Uniques Close" class="icon close-icon">
            <!--    <strong>Uniques</strong>-->
            </button>    
            <div class="content">   
                <div id="uniques" class="container">
                    <div class="column">
                        <h3>Most Used Uniques:</h3>
                        <ul id="most-popular-uniques">
                            {most_popular_uniques}
                        </ul>
                    </div>
                    <div class="column">
                        <h3>Least Used Uniques:</h3>
                        <ul id="least_popular_uniques">
                            {least_popular_uniques}
                        </ul>
                    </div>
                </div>
                <button type="button" class="collapsible small-collapsible">
                    <img src="icons/open.png" alt="All Uniques Open" class="icon-small open-icon hidden">
                    <img src="icons/closed.png" alt="Uniques Close" class="icon-small close-icon">
                    <strong>ALL Uniques</strong>
                </button>

                <div class="content">
                    <div id="alluniques">
                        {all_uniques}
                    </div>
                </div>

            </div>

            <br>
            <button type="button" class="collapsible sets-button">
                <img src="icons/Sets_click.png" alt="Sets Open" class="icon open-icon hidden">
                <img src="icons/Sets.png" alt="Sets Close" class="icon close-icon">
            <!--    <strong>Sets</strong>-->
            </button>  
            <div class="content">  
                <div id="sets" class="container">
                    <div class="column">
                        <h3>Most Used Set Items:</h3>
                        <ul id="most-popular-set-items">
                            {most_popular_set_items}
                        </ul>
                    </div>
                    <div class="column">
                        <h3>Least Used Set Items:</h3>
                        <ul id="least_popular_set_items">
                            {least_popular_set_items}
                        </ul>
                    </div>
                </div>
                <button type="button" class="collapsible small-collapsible">
                    <img src="icons/open.png" alt="All Set Open" class="icon-small open-icon hidden">
                    <img src="icons/closed.png" alt="Set Close" class="icon-small close-icon">
                    <strong>ALL Set</strong>
                </button>

                <div class="content">
                    <div id="allset">
                        {all_set}
                    </div>
                </div>
            </div>
            <br>
                    <h2>Synth reporting</h2>
                    <h2>{synth_user_count} Characters with Synthesized items equipped</h2>
                    <h3>This is base synthesized items</h3>
            <button type="button" class="collapsible sets-button">
                <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
                <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
            <!--    <strong>Sets</strong>-->
            </button>  
            <div class="content">  
                    <div id="special">
                        {all_synth}
                    </div>
                </div>

                    <h2>{synth_source_user_count} Synthesized FROM listings</h2>
                    <h3>This shows where propertied an item are showing up in other items. If you wanted to see where the slow from Kelpie or the Ball light from Ondal's had popped up, this is where to look </h3>
            <button type="button" class="collapsible sets-button">
                <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
                <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
            <!--    <strong>Sets</strong>-->
            </button>  
            <div class="content">  
                    <div id="special">
                        {synth_source_data}
                    </div>
                </div>


                    <br>

                    <h2>Craft reporting</h2>
                    <h3>{craft_user_count} Characters with crafted items equipped</h3>

            <button type="button" class="collapsible sets-button">
                <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
                <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
            <!--    <strong>Sets</strong>-->
            </button>  
            <div class="content">  
                    <div id="special">
                        {all_crafted}
                    </div>
                </div>

            <br>

            <br>
                    <h2>Magic reporting</h2>
                    <h3>{magic_user_count} Characters with Magic items equipped</h3>

            <button type="button" class="collapsible sets-button">
                <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
                <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
            <!--    <strong>Sets</strong>-->
            </button>  
            <div class="content">  
                    <div id="special">
                        {all_magic}
                    </div>
                </div>

            <br>

                    <h2>Rare reporting</h2>
                    <h3>{rare_user_count} Characters with rare items equipped</h3>

            <button type="button" class="collapsible sets-button">
                <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
                <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
            <!--    <strong>Sets</strong>-->
            </button>  
            <div class="content">  
                    <div id="special">
                        {all_rare}
                    </div>
                </div>

            <br>

                    <h2>Socketable reporting</h2>
                    <h3>What are people puting in sockets</h3>

            <button type="button" class="collapsible sets-button">
                <img src="icons/Special_click.png" alt="Synth Open" class="icon open-icon hidden">
                <img src="icons/Special.png" alt="Synth Close" class="icon close-icon">
            <!--    <strong>Sets</strong>-->
            </button>  
            <div class="content">  
                    <h2>Socketed Runes Count</h2>
                    <h3>Includes Only Character Data, No Mercs</h3>
                <div id="special"  class="container">
            <br>
                    <div class="column">
                        <!-- Left Column -->
                            <h2>Most Common Runes <br>(Including Runewords)</h2>
                        <ul id="sorted_just_socketed_runes"
                            {sorted_just_socketed_runes}
                        </ul>
                        </div>

                        <!-- Right Column -->
                        <div class="column">
                            <h2>Most Common Runes <br>(Excluding Runewords)</h2>
                        <ul id="sorted_just_socketed_excluding_runewords_runes">
                            {sorted_just_socketed_excluding_runewords_runes}
                        </ul>
                        </div>
                    </div>

                    <div>
                        <h2>Other Items Found in Sockets</h2>
                    <h3>Includes Only Character Data, No Mercs</h3>
                        {all_other_items}
                    </div>
                </div>
<hr>
                                    <h1>Mercenary reporting</h1>
                    <h3>Mercenary counts and Most Used Runewords, Uniques, and Set items equipped</h3>

                    <button type="button" class="collapsible">
                        <img src="icons/Merc_click.png" alt="Merc Details Open" class="icon open-icon hidden">
                        <img src="icons/Merc.png" alt="Merc Details Close" class="icon close-icon">
            <!--            <strong>Mercenary Details</strong> -->
                    </button>
                    <div class="content">
                    <div id="mercequips">
                        {html_output}
                    </div>
                    </div>
            
            <hr>
            {{ fun_facts_html }}
            <hr>
            <!-- Embed the Plotly scatter plot -->
            <div>
                <img src="charts/{{ what_class }}-clusters_with_avg_points.png" alt="{{ what_class }} Skill Clusters Scatter Plot">
            </div>
            <button onclick="topFunction()" id="backToTopBtn" class="back-to-top"></button>

            <div class="footer">
            <p>PoD class data current as of {{ timeStamp }}</p>
            </div>            



<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var openIcon = this.querySelector("img.icon[alt='Open']");
        var closeIcon = this.querySelector("img.icon[alt='Close']");

        if (content.style.display === "block") {
            content.style.display = "none";
            openIcon.classList.remove("hidden");
            closeIcon.classList.add("hidden");
        } else {
            content.style.display = "block";
            openIcon.classList.add("hidden");
            closeIcon.classList.remove("hidden");
        }
    });
}


//Get the button
var backToTopBtn = document.getElementById("backToTopBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
backToTopBtn.style.display = "block";
} else {
backToTopBtn.style.display = "none";
}
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
document.body.scrollTop = 0; // For Safari
document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function toggleMenu() {
    const navMenu = document.querySelector('.top-buttons');
    navMenu.classList.toggle('show');
}


document.addEventListener("DOMContentLoaded", function () {
const scHcButton = document.getElementById("SC_HC");
const currentUrl = window.location.href;
const filename = currentUrl.split("/").pop(); // Get the last part of the URL

// Check if the current page is Hardcore or Softcore
const isHardcore = filename.startsWith("hc");

// Update button appearance based on current mode
if (isHardcore) {
scHcButton.classList.add("hardcore");
scHcButton.classList.remove("softcore");
} else {
scHcButton.classList.add("softcore");
scHcButton.classList.remove("hardcore");
}

// Update background image based on mode
updateButtonImage(isHardcore);

// Add click event to toggle between SC and HC pages
scHcButton.addEventListener("click", function () {
let newUrl;

if (isHardcore) {
// Convert HC -> SC (remove "hc" from filename)
newUrl = currentUrl.replace(/hc(\w+\.html)$/, "$1");
} else {
// Convert SC -> HC (prepend "hc" to the filename)
newUrl = currentUrl.replace(/(\w+\.html)$/, "hc$1");
}

// Redirect to the new page
if (newUrl !== currentUrl) {
window.location.href = newUrl;
}
});

// Function to update button background image
function updateButtonImage(isHardcore) {
if (isHardcore) {
scHcButton.style.backgroundImage = "url('icons/Hardcore_click.png')";
} else {
scHcButton.style.backgroundImage = "url('icons/Softcore_click.png')";
}
}
});

document.addEventListener("DOMContentLoaded", function () {
const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
const menuItems = document.querySelectorAll(".top-button");

menuItems.forEach(item => {
const itemPage = item.getAttribute("href");
if (itemPage && currentPage === itemPage) {
item.classList.add("active");
}
});
});


document.addEventListener("DOMContentLoaded", function () {
let activePopup = null;

document.querySelectorAll(".hover-trigger").forEach(trigger => {
trigger.addEventListener("click", function (event) {
event.stopPropagation();
const characterName = this.getAttribute("data-character-name");

// Close any open popup first
if (activePopup) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe for memory efficiency
activePopup = null;
}

// Find the associated popup container
const popup = this.closest(".character-info").nextElementSibling.querySelector(".popup");

// If this popup was already active, just close it
if (popup === activePopup) {
return;
}

// Create an iframe and set its src
const iframe = document.createElement("iframe");
iframe.src = `./armory/video_component.html?charName=${encodeURIComponent(characterName)}`;
iframe.setAttribute("id", "popupFrame");

// Add iframe to the popup
popup.appendChild(iframe);
popup.classList.add("active");

// Set this popup as the active one
activePopup = popup;
});
});

// Close the popup when clicking anywhere outside
document.addEventListener("click", function (event) {
if (activePopup && !activePopup.contains(event.target)) {
activePopup.classList.remove("active");
activePopup.innerHTML = ""; // Remove iframe to free memory
activePopup = null;
}
});
});

</script>





        </body>
        </html>
        """

        def analyze_mercenaries(filtered_characters):
            mercenary_counts = Counter()
            mercenary_equipment = defaultdict(lambda: defaultdict(Counter))
            mercenary_names = Counter()

            for char_data in filtered_characters:
                if not isinstance(char_data, dict):
                    print(f"Skipping unexpected data format: {char_data}")
                    continue  # Skip invalid entries

                mercenary = char_data.get("MercenaryType")
                if mercenary:
                    readable_mercenary, _ = map_readable_names(mercenary, "")
                    mercenary_counts[readable_mercenary] += 1

                    merc_name = char_data.get("MercenaryName", "Unknown")
                    mercenary_names[merc_name] += 1

                    for item in char_data.get("MercenaryEquipped", []):
                        worn_category = item.get("Worn", "Unknown")
                        readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                        title = item.get("Title", "Unknown")
                        mercenary_equipment[readable_mercenary][readable_worn][title] += 1

            return mercenary, mercenary_counts, mercenary_equipment, mercenary_names

    #        output_file = "all_mercenary_report.html"

        # Function to generate the HTML report
        def generate_mercenary_report(filtered_characters):
            _, mercenary_counts, mercenary_equipment, mercenary_names = analyze_mercenaries(filtered_characters)  # Ignore first return value

            html_output = "<p><h2>Mercenary Analysis and Popular Equipment</h2></p>"

            # Mercenary type counts
            html_output += "<p><h3>Mercenary Type Counts</h3></p><ul>"
            for mercenary, count in mercenary_counts.items():
                html_output += f"<li>{mercenary}: {count}</li>"
            html_output += "</ul>"

            # ✅ This now works!
            html_output += "<h3>Most Common Mercenary Names</h3><ul>"
            for name, count in mercenary_names.most_common(10):
                html_output += f"<li>{name}: {count}</li>"
            html_output += "</ul>"

            # Popular Equipment by Mercenary Type
            html_output += "<p><h3>Popular Equipment by Mercenary Type</h3></p>"
            for mercenary, categories in mercenary_equipment.items():
                html_output += f"<div class='row'><p><strong>{mercenary}</strong></p>"
                for worn_category, items in categories.items():
                    html_output += f"<div class='merccolumn'><strong>Most Common {worn_category}s:</strong>"
                    html_output += "<ul>"
                    top_items = items.most_common(15)  # Get the top 10 items
                    for title, count in top_items:
                        html_output += f"<li>{title}: {count}</li>"
                    html_output += "</ul></div>"
                html_output += "</div>"

            return html_output

        # Load the consolidated JSON file
        with open("sc_ladder.json", "r") as file:
            all_characters = json.load(file)

        # Generate the report
        html_output = generate_mercenary_report(filtered_characters)

        # Assuming df is your DataFrame and skill_columns contains the column names for the skills

        # Calculate the total usage of each skill across all clusters
        total_skill_usage = df[skill_columns].sum()

        # Sort skills by total usage in descending order
        most_used_skills = total_skill_usage.sort_values(ascending=False)

        # Sort skills by total usage in ascending order
        least_used_skills = total_skill_usage.sort_values(ascending=True)

        # Extract the top 5 most used skills
        top_5_most_used_skills = most_used_skills.head(5)

        # Extract the bottom 5 least used skills
        bottom_5_least_used_skills = least_used_skills.head(5)


        # Calculate the percentage of characters that have invested in each skill within the cluster
        skill_percentages = df[skill_columns].astype(bool).groupby(df['Cluster']).mean() * 100

        # Identify the top skills per cluster with their average points and percentages
        top_skills_with_avg_and_percent = skill_averages.apply(lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) for skill in x.nlargest(howmany_skills).index], axis=1)


        # Define skill weights
        skill_weights = {
            ### Amazon
            ### Assassin
            "Dragon Talon": 100,
            "Dragon Flight": 30,
            "Mind Blast": 100, 
            "Psychic Hammer": 100,
            ### Barb
            "Bash": 50,
            "Cleave": 50,
            "Whirlwind": 100,
            "Double Swing": 50,
            "War Cry": 70,
            ### Druid
            ### Necro
            "Hemorrhage": 70,
            ### Paladin
            "Fist of the Heavens":80,
            "Zeal": 30,
            "Dashing Strike": 50,
            "Smite": 50,
            "Charge": 50,
            "Holy Bolt": 70,
            ### Sorceress
            "Telekinesis": 50,
            "Thunder Storm": 80,
            "Lightning Surge": 100,
            "Nova": 50,
            "Charged Bolt": 100,
            "Blizzard": 100,
            "Frigerate": 100,
            "Freezing Pulse": 100,
            "Frozen Orb": 100,
            "Frost Nova": 50,
            "Hydra": 100,
            "Meteor": 100,
            "Enflame": 100,
            "Immolate": 50,
            "Inferno": 80
        }

        # Define your existing top_skills_with_avg_and_percent
        top_skills_with_avg_and_percent = skill_averages.apply(
            lambda x: [(skill, round(x[skill], 2), round(skill_percentages.loc[x.name, skill], 2)) 
                    for skill in x.nlargest(howmany_skills).index], axis=1)

        # Sort skills by weights immediately after defining top_skills_with_avg_and_percent
        top_skills_with_avg_and_percent = top_skills_with_avg_and_percent.apply(
            lambda skill_list: sorted(skill_list, key=lambda skill: -skill_weights.get(skill[0], 0))
        )

        summary_label = ""
        summaries = []
        
        def generate_summary(clusters, class_name):
            skill_weights = {
                "Telekinesis": 5,
                "Thunder Storm": 8,
                "Lightning Surge": 10,
                "Nova": 5,
                "Charged Bolt": 10,
                "Blizzard": 10,
                "Frigerate": 10,
                "Freezing Pulse": 10,
                "Frozen Orb": 10,
                "Frost Nova": 5,
                "Hydra": 10,
                "Meteor": 10,
                "Enflame": 10
            }

            summaries = []

            for cluster, data in clusters.items():
                cluster_percentage = data["character_count"] / sum(c["character_count"] for c in clusters.values()) * 100
                top_skills = data["label"].split("<br>")  # Extract skills

                # Assign weights & sort by importance
                weighted_skills = sorted(
                    top_skills, 
                    key=lambda skill: skill_weights.get(skill.split()[0], 1), 
                    reverse=True
                )

                # Format the summary
                summary = f"{cluster_percentage:.2f}% of {class_name}s favor " + ", ".join(weighted_skills)
                summaries.append((cluster_percentage, summary))

            return summaries

#        data_folder = "sc/ladder-all"

        # Gather data for the report
        clusters = {}
        for cluster, group in df.groupby('Cluster'):
            sorted_group = group.sort_values(by='Level', ascending=False)  # Sort by level descending
            character_count = len(sorted_group)
            cluster_percentage = cluster_counts[cluster]
            equipment_counts = {}

            # Later processing (example, adjust as needed)
            for row in sorted_group.itertuples():
                equipment_list = row.Equipment.split(", ")
                for item in equipment_list:
                    if item:
                        worn, title_count = item.split(": ", 1)
                        if " x" in title_count:
                            title, count = title_count.split(" x", 1)
                            count = int(count)
                        else:
                            title = title_count
                            count = 1

                        if worn not in equipment_counts:
                            equipment_counts[worn] = {}
                        if title in equipment_counts[worn]:
                            equipment_counts[worn][title] += count
                        else:
                            equipment_counts[worn][title] = count  # Initialize with real count


#            print("🔹 Original Equipment Counts:")
#            pp.pprint(equipment_counts)

            # Extract character file paths for this cluster
            cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
            cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

            # Get mercenary data **just for this cluster**
            _, mercenary_counts, mercenary_equipment, mercenary_names = analyze_mercenaries(filtered_characters)

            # Generate HTML report for mercenaries in this cluster
            merc_count = f"<h3>Mercenary Equipment Analysis for Cluster {cluster}</h3>"

            # Mercenary type counts
            merc_count += "<h4>Count of Mercenary Types</h4>"
            for mercenary, count in mercenary_counts.items():
                merc_count += f"<p>{mercenary}: {count}</p>"

            # Mercenary equipment titles
            merc_count += "<h4>Equipment Titles</h4>"
            for mercenary, equipment in mercenary_equipment.items():
                merc_count += f"<p><strong>{mercenary}:</strong></p>"
                for title, count in equipment.items():
                    merc_count += f"<p>{title}: {count}</p>"

            # ✅ Fix: Ensure the cluster exists before adding merc_count
            if cluster not in clusters:
                clusters[cluster] = {}

            if 'merc_count' not in clusters[cluster]:
                clusters[cluster]['merc_count'] = merc_count

            # Calculate total counts for each category
            total_counts = {
                worn: sum(titles.values())
                for worn, titles in equipment_counts.items()
            }

            # Calculate the percentages based on total counts
            equipment_percentages = {
                worn: {title: (count / total_counts[worn]) * 100 for title, count in titles.items()}
                for worn, titles in equipment_counts.items()
            }

            # Get top equipment based on count
            top_equipment = {
                worn: sorted(titles.items(), key=lambda item: item[1], reverse=True)[:5]
                for worn, titles in equipment_counts.items()
            }

            # Use equipment_percentages for display
            top_equipment_str_list = []
            for worn, titles in top_equipment.items():
                titles_str = "<br>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;{title} {equipment_percentages[worn][title]:.2f}% ({count})" for title, count in titles])
                top_equipment_str_list.append(f"<strong>{worn.capitalize()}</strong>: <br>{titles_str}")

            top_equipment_str = "<br>".join(top_equipment_str_list)

            # Use sorted_equipment_counts for full display
            sorted_equipment_counts = {
                worn: dict(sorted(titles.items(), key=lambda item: item[1], reverse=True))
                for worn, titles in equipment_counts.items()
            }

            equipment_counts_str_list = []
            for worn, titles in sorted_equipment_counts.items():
                titles_str = ", ".join([f"{title} {equipment_percentages[worn][title]:.2f}%" for title in titles])
                equipment_counts_str_list.append(f"<strong>{worn.capitalize()}</strong>: {titles_str}")

            equipment_counts_str = "<br>".join(equipment_counts_str_list)

            # Output results
#            print(top_equipment_str)
#            print(equipment_counts_str)


            # Define a helper function to format numbers
            def format_number(num):
                return int(num) if num % 1 == 0 else round(num, 2)

            # Filter top skills
            top_skills = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]

            # Filter other skills, ignoring those with zero points
            other_skills = skill_averages.loc[cluster].drop(top_skills)
            other_skills = other_skills[other_skills > 0].nlargest(6)
            other_skills_pie = "<br>".join([f"{skill} ({format_number(avg)})" for skill, avg in other_skills.items()])
#            other_skills_str = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(other_skills[skill] * character_count)})" for skill in other_skills.index])
            other_skills_str = "<br>".join([
                f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
                f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
                f"({format_number(other_skills[skill] * character_count)})</span>"
                for skill in other_skills.index
            ])
            # Filter remaining skills, ignoring those with zero points
            remaining_skills = skill_averages.loc[cluster].sort_values(ascending=False)
            remaining_skills = remaining_skills[remaining_skills > 0]
#            remaining_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
            remaining_skills_str2 = "<br>".join([
                f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                f"<span class='{'highlight-100' if round(skill_percentages.loc[cluster, skill], 2) == 100 else 'normal-skill'}'>"
                f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% "
                f"({format_number(remaining_skills[skill] * character_count)})</span>"
                for skill in remaining_skills.index
            ])


#            remaining_skills_str_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})" for skill in remaining_skills.index])
            # Group the skills into chunks of 5
            # Group skills into chunks of 10, with each row containing 2 skills
            remaining_skills_str_with_icons = "\n".join([
                "<div class='skills-group'>" + "\n".join([
                    "<div class='skills-row'>" +
                    "\n".join([
                        f"<div class='skill-item'>"
                        f"<div class='skillbar-container'>"
                        f"<div class='skill-info'>"
                        f"<img src='{icons_folder}/{skill}.png' alt='{skill}' class='skill-icon'> "
                        f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({format_number(remaining_skills[skill] * character_count)})"
                        f"</div>"
                        f"<div class='skill-mini-bar' style='width: {round(skill_percentages.loc[cluster, skill], 2) * 4}px;'></div>"
                        f"</div>"
                        f"</div>"
                        for skill in remaining_skills.index[row:row+2]
                    ]) +
                    "</div>"  # Close row
                    for row in range(i, min(i+10, len(remaining_skills.index)), 2)
                ]) + "</div>"  # Close group
                for i in range(0, len(remaining_skills.index), 10)
            ])

        #    all_skills_str2 = "<br>".join([f"{skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
        #    all_skills_str2_with_icons = "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {round(skill_percentages.loc[cluster, skill], 2)}% ({round(remaining_skills[skill] * character_count, 2)})" for skill in all_skills.index])
            sorted_summary_label = ""
            summary_labels = [skill for skill, _, _ in top_skills_with_avg_and_percent[cluster]]
            summary = f"&nbsp;&nbsp;- {cluster_percentage:.2f}% use " + ", ".join(summary_labels)
#            summary = f"{cluster_percentage:.2f}% of {what_class}'s invest heavily in " + ", ".join(summary_labels)
            summaries.append((cluster_percentage, summary))

            clusters[cluster] = {
                'label': f"{cluster_percentage:.2f}% of {what_class}'s Main Skills:<br>" + "".join([
                    f"""
                    <div class="skillbar-container">
                        <div class="skill-row">
                            <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                            <div class="skill-bar-container">
                                <div class="skill-bar" >
                                    <span class="skill-label">{skill} ({int(avg * character_count)})</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                    for skill, avg, percent in top_skills_with_avg_and_percent[cluster]
                ]),

                'character_count': character_count,
                'other_skills': other_skills_str,
                'other_skills_pie': other_skills_pie,
                'characters': [
                    {
                        'name': row.Name, 'level': row.Level, 'skills': row.Skills,
                        'equipment': row.Equipment, 'mercenary': row.Mercenary,
                        'mercenary_equipment': row.MercenaryEquipment, 'class': row.Class
                    } 
                    for row in sorted_group.itertuples()
                ],
                'top_equipment': top_equipment_str,  
                'equipment_counts': equipment_counts_str,
                'remaining_skills_with_icons': remaining_skills_str_with_icons,
                'remaining_skills_str2': remaining_skills_str2,  
                'top_5_most_used_skills': top_5_most_used_skills,
                'bottom_5_least_used_skills': bottom_5_least_used_skills,
                'summary_label': summary_label, 
                'mercenary': mercenary,  
                'mercenary_equipment': mercenary_equipment,
            }
            _, mercenary_counts, mercenary_equipment, mercenary_names = analyze_mercenaries(filtered_characters)
    

        # Ensure the correct percentage values are used
        pie_data = df.groupby('Cluster').agg({
            'Percentage': 'mean',  # Get the mean percentage for each cluster
            'Cluster_Label': 'first'  # Use the first cluster label as representative
        }).reset_index()

        # Include other_skills in customdata
        pie_data['other_skills_pie'] = pie_data['Cluster'].map(lambda cluster: clusters[cluster]['other_skills_pie'])

        # Combine cluster label and percentage for the pie chart labels
        pie_data['Cluster_Label_Percentage'] = pie_data.apply(lambda row: f"{row['Percentage']:.2f}% - Main Skills and avg points: {row['Cluster_Label']}", axis=1)

        import plotly.express as px

        # Get unique clusters
        unique_clusters = sorted(df['Cluster'].unique())  # Sorting ensures consistent ordering

        # Assign colors from a predefined palette
        color_palette = px.colors.qualitative.Safe  # You can change this to Vivid, Bold, etc.
        color_map = {cluster: color_palette[i % len(color_palette)] for i, cluster in enumerate(unique_clusters)}

        # Create a pie chart
        fig_pie = px.pie(
            pie_data,
            values='Percentage',
            names='Cluster_Label_Percentage',
            title=f"{what_class} Skills Distribution",
            hover_data={'Cluster_Label': True, 'other_skills_pie': True},
            color_discrete_map={row['Cluster_Label_Percentage']: color_map[row['Cluster']] for _, row in pie_data.iterrows()}  # ✅ Maps labels to the same colors
        )

        # Update customdata to pass Cluster_Label
        fig_pie.update_traces(customdata=pie_data[['Cluster_Label', 'other_skills_pie']])

        # Customize the hover template for the pie chart
        fig_pie.update_traces(
            textinfo='percent',  # Keep percentages on the pie slices
            textposition='inside',  # Position percentages inside the pie slices
            hovertemplate="<b>%{customdata[0]}</b><br>Other Skills and Average Point Investment:<br>%{customdata[1]}<extra></extra>",
            marker=dict(line=dict(color='black', width=1)),  # Add a slight outline for clarity
            pull=[0.05] * len(pie_data),  # Slightly pull slices apart to increase visibility
            hole=0  # Ensure it's a full pie (not a donut)
        )

        # Position the legend outside the pie chart and adjust the pie chart size
        fig_pie.update_layout(
            legend=dict(
                orientation="h",  # Horizontal legend
                yanchor="top",
                y=-0.15,  # Move it closer
                xanchor="center",
                x=0.5,  # Keep it centered
                font=dict(size=10, color='white'),
                bgcolor='rgba(0,0,0,0)',
#                font=dict(color='white'),  # ✅ Transparent background
            ),
            paper_bgcolor='rgba(0,0,0,0)', # ✅ Transparent background
            margin=dict(l=10, r=10, t=50, b=20),  # Reduce bottom margin to make more space
            width=900,  # Set the width of the entire chart
            height=600,  # Set the height of the entire chart
            font=dict(color='white'),  # ✅ Makes all text white
            title=dict(font=dict(color='white')),  # ✅ Ensures title is also white
#            legend=dict(font=dict(color='white'))  # ✅ Ensures legend text is white
        )

        # Increase the pie size explicitly
        fig_pie.update_traces(domain=dict(x=[0, 1], y=[0.1, 1]))  # Expands pie upward

        # Save the pie chart as a PNG file
        fig_pie.write_image(f"pod-stats/charts/{what_class}-clusters_distribution_pie.png")

        # Create a DataFrame for visualization
        plot_data = pd.DataFrame({
            'PCA1': reduced_data[:, 0],
            'PCA2': reduced_data[:, 1],
            'Cluster': df['Cluster'],
            'Cluster_Label': df['Cluster_Label'],
            'Percentage': df['Percentage']
        })

        # Create an interactive scatter plot
        fig_scatter = px.scatter(
            plot_data,
            x='PCA1',
            y='PCA2',
            color='Cluster',  # Assign color based on the cluster
            title=f"{what_class} Skill Clusters (Ladder Top 200 {what_class}'s Highlighted)<br>This highlights how similar (or not) a character is to the rest<br>The tighter the grouping, the more they are alike",
            hover_data={'Cluster_Label': True, 'Percentage': ':.2f%', 'Cluster': True},
            color_discrete_map=color_map  # Use the same colors as the pie chart
        )

        # Customize the legend labels
        for trace in fig_scatter.data:
            if trace.name.isnumeric():  # Ensure that the trace name is numeric
                trace.update(name=legend_labels[int(trace.name)])

        # Customize hover template to include top skills and percentage
        fig_scatter.update_traces(
            hovertemplate="<b>Cluster skills and average point investment:</b><br> %{customdata[0]}<br>" +
                        "This cluster (%{customdata[2]}) makes up %{customdata[1]:.2f}% of the total<extra></extra>"
        )

        # Hide the axis titles and tick labels
        fig_scatter.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            xaxis_showticklabels=False,
            yaxis_showticklabels=False
        )

        # Save the scatter plot as a PNG file
        fig_scatter.write_image(f"pod-stats/charts/{what_class}-clusters_with_avg_points.png")

        print("Pie chart and scatter plot saved as PNG files.")

        # Sort clusters by percentage in descending order
        sorted_clusters = dict(sorted(clusters.items(), key=lambda item: item[1]['character_count'], reverse=True))

        # Split the entries into a list
        entries = summary_label.strip().split("<br>\n")
        # Remove any empty strings from the list (if any)
        entries = [entry for entry in entries if entry.strip()]
        # Sort the entries in descending order based on the percentage value
        sorted_entries = sorted(entries, key=lambda x: float(x.split('%')[0]), reverse=False)
        # Join the sorted entries back into a single string
        sorted_summaries = sorted(summaries, key=lambda x: x[0], reverse=True)

        skill_tree_mappings = {
            "Amazon": {
                "Javelin & Spear": {"Lightning Fury", "Charged Strike", "Jab", "Power Strike", "Plague Javelin", "Poison Javelin", "Fend"},
                "Bow & Crossbow": {"Multiple Shot", "Immolation Arrow", "Freezing Arrow", "Fire Arrow", "Exploding Arrow", "Guided Arrow", "Magic Arrow", "Strafe"},
            },
            "Assassin":{
                "Martial Arts": {"Claws of Thunder", "Fists of Fire", "Blades of Ice"},
                "Trap": {"Wake of Fire", "Wake of Inferno", "Lightning Sentry", "Death Sentry", "Charged Bolt Sentry", "Shock Web"},
        #        "Lightning Traps": {"Lightning Sentry", "Death Sentry", "Charged Bolt Sentry", "Shock Web"},

            },
            "Barbarian":{
                "Warcry": {"War Cry"},
                "Throw": {"Ethereal Throw", "Double Throw"},
                "Whirling Axes": {"Whirling Axes", "Battle Cry"},
                "Combat": {"Cleave", "Concentrate", "Bash", "Frenzy"},
                "Whirlwind": {"Whirlwind"},
            },
            "Sorceress": {
                "The Best Sorc Skills": {"Frigerate", "Enflame"},
#                "Hybrid Skills": {"Blizzard", "Hydra"} ,
#                "Hybrid Skills": {"Frozen Orb", "Hydra"},
#                "Hybrid Skills": {"Freezing Pulse", "Hydra"},
                "Cold Spells": {"Freezing Pulse", "Frozen Orb", "Blizzard", "Ice Bolt", "Cold Mastery", "Glacial Spike"},
                "Lightning Spells": {"Nova", "Lightning", "Chain Lightning", "Lightning Mastery", "Thunder Storm"},
                "Fire Spells": {"Fire Ball", "Meteor", "Hydra", "Fire Mastery", "Enflame"},
            },
            "Paladin": {
                "FoH Builds": {"Fist of the Heavens", "Holy Bolt"},
                "Combat Builds": {"Smite", "Charge", "Zeal", "Dashing Strike"},
                "Hammerdins": {"Blessed Hammer", "Blessed Aim"}
        #        "Offensive Auras": {"Fanaticism", "Conviction", "Holy Fire", "Holy Shock"},
        #        "Defensive Auras": {"Defiance", "Resist Fire", "Resist Cold", "Resist Lightning"},
            },
            "Necromancer": {
        #        "CE": {"Corpse Explosion"},
                "Poison & Bone": {"Bone Spear", "Bone Spirit", "Poison Nova", "Teeth", "Corpse Explosion", "Deadly Poison"},
                "Summoning": {"Raise Skeleton", "Skeleton Mastery", "Revive", "Clay Golem", "Fire Golem"},
                "Curses": {"Hemorrhage", "Amplify Damage", "Decrepify", "Lower Resist", "Iron Maiden"},
            },
            "Druid": {
                "Elemental": {"Hurricane", "Tornado", "Firestorm", "Molten Boulder"},
                "Shape Shifting": {"Werewolf", "Werebear", "Feral Rage", "Maul"},
                "Summoning": {"Raven", "Summon Grizzly", "Summon Dire Wolf"},
            },
        }
        # Function to sort builds into categories
        def organize_by_skill_tree(class_name, sorted_summaries):
            if class_name not in skill_tree_mappings:
                return "<br>".join(f"{pct:.2f}% {summary}" for pct, summary in sorted_summaries)

            skill_trees = skill_tree_mappings[class_name]
            tree_investment = {tree: 0 for tree in skill_trees}
            sorted_builds = {tree: [] for tree in skill_trees}

            for pct, summary in sorted_summaries:
                assigned_tree = None
                for tree, skills in skill_trees.items():
                    if any(skill in summary for skill in skills):
                        assigned_tree = tree
                        break  # Only assign once

                if assigned_tree:
                    tree_investment[assigned_tree] += pct
                    sorted_builds[assigned_tree].append(f" {summary}")  # ✅ Remove unnecessary breaks

            final_summary = []
            for tree, pct in tree_investment.items():
                if pct > 0:
                    final_summary.append(f"<br><strong>{pct:.2f}% of all {class_name}s favor {tree} </strong>")
                    final_summary.extend(sorted_builds[tree])  # ✅ Ensures builds are close to category header

            return "<br>".join(final_summary)  # ✅ Join without excessive spacing
        
        organize_by_skill_tree(what_class, sorted_summaries)

        amazon_summary =  ""       
        amazon_summary = ""
        assassin_summary = ""
        barbarian_summary = ""
        druid_summary = ""
        necromancer_summary = ""
        paladin_summary = ""
        sorceress_summary = ""

#        amazon_summary = "<br><strong>46% of all Amazons favor Spear and Javelin Skills</strong><br>" \
#                        "<strong>54% of all Amazons favor Bow Skills</strong><br><br>More detailed breakdown:<br>"
#        assassin_summary = "<br><strong>70% of all Assasins favor Wof/WoI</strong><br>" \
#                        "<strong>16% of all Assasins favor Martial Arts</strong><br><br>More detailed breakdown:<br>"
#        barbarian_summary = "<br><strong>50% of all Barbs favor Whirling Axes</strong><br>" \
#                        "<strong>3% of all Barbs favor Throwing</strong><br><br>More detailed breakdown:<br>"
#        druid_summary = "<br><strong>40% of all Druids favor Shapeshifting</strong><br>" \
#                        "<strong>30% of all Druids favor Summons</strong><br>" \
#                        "<strong>30% of all Druids favor Elemental Skills</strong><br><br>More detailed breakdown:<br>"
#        necromancer_summary = "<br><strong>52% of all Necros favor Hemo</strong><br>" \
#                        "<strong>32% of all Necros favor CE</strong><br><br>More detailed breakdown:<br>"
#        paladin_summary = "<br><strong>43% of all Paladins favor FoH</strong><br>" \
#                        "<strong>21% of all Paladins are Hammerdins</strong><br><br>More detailed breakdown:<br>"
#        sorceress_summary = "<br><strong>42% of all Sorcs favor Lightning</strong><br>" \
#                        "<strong>42% of all Sorcs favor Cold</strong><br>" \
#                        "<strong>14% of all Sorcs favor Fire</strong><br><br>More detailed breakdown:<br>"
        
        structured_summary = organize_by_skill_tree(what_class, sorted_summaries)

        if what_class == "Amazon":
            summary_label = amazon_summary + "<br>".join(summary for _, summary in sorted_summaries)
            structured_summary_label = amazon_summary + "" + structured_summary
        elif what_class == "Assassin":
            summary_label = assassin_summary + "<br>".join(summary for _, summary in sorted_summaries)
            structured_summary_label = assassin_summary + "" + structured_summary
        elif what_class == "Barbarian":
            summary_label = barbarian_summary + "<br>".join(summary for _, summary in sorted_summaries)
            structured_summary_label = barbarian_summary + "" + structured_summary
        elif what_class == "Druid":
            summary_label = druid_summary + "<br>".join(summary for _, summary in sorted_summaries)
            structured_summary_label = druid_summary + "" + structured_summary
        elif what_class == "Necromancer":
            summary_label = necromancer_summary + "<br>".join(summary for _, summary in sorted_summaries)
            structured_summary_label = necromancer_summary + "" + structured_summary
        elif what_class == "Paladin":
            summary_label = paladin_summary + "<br>".join(summary for _, summary in sorted_summaries)
            structured_summary_label = paladin_summary + "" + structured_summary
        elif what_class == "Sorceress":
            summary_label = sorceress_summary + "<br>".join(summary for _, summary in sorted_summaries)
            structured_summary_label = sorceress_summary + "" + structured_summary
        else:
            structured_summary_label = structured_summary  # Default case

        # Combine both versions for side-by-side comparison
        full_summary_output = f"""
        <h2>Build Trends</h2>
        <p>{structured_summary_label}</p>
        <hr>
        <h2>Detailed Grouping Information, Ordered Highest to Lowest %</h2>
        <p>{summary_label}</p>
        """
#        else: 
#            summary_label = "<br>".join(summary for _, summary in sorted_summaries)

#        summary_label = "<br>".join(summary for _, summary in sorted_summaries)
        #print(summary_label)

        # Ensure the cluster exists before adding merc_count
        if cluster not in clusters:
            clusters[cluster] = {}

        clusters[cluster]['merc_count'] = merc_count

    #    print(f"✅ Added merc data for cluster {cluster}:")
    #    print(merc_count)

        dt = datetime.now()
        # format it to a string
        timeStamp = dt.strftime('%Y-%m-%d %H:%M')

        with open("sc_ladder.json", "r") as file:
            all_characters = json.load(file)

        sorted_runes, sorted_excluding_runes, all_other_items = socket_html(filtered_characters)

        # Render the HTML report
        template = Template(html_template)
        html_content = template.render(clusters=sorted_clusters, 
                                       what_class=what_class, 
                                       top_5_most_used_skills=top_5_most_used_skills, 
                                       bottom_5_least_used_skills=bottom_5_least_used_skills, 
                                       summary_label=summary_label, merc_count=merc_count, 
                                       mercenary=mercenary, mercenary_equipment=mercenary_equipment, 
                                       timeStamp=timeStamp, full_summary_output=full_summary_output, 
                                       fun_facts_html=fun_facts_html
                                       )  # Pass sorted clusters to the template


        socketed_runes_html, socketed_excluding_runes_html, other_items_html = socket_html(filtered_characters)

        filled_html_content = f"""{html_content}""".replace(
                "{most_popular_runewords}", generate_list_items(most_common_runewords)
            ).replace(
                "{most_popular_uniques}", generate_list_items(most_common_uniques)
            ).replace(
                "{most_popular_set_items}", generate_list_items(most_common_set_items)
            ).replace(
                "{least_popular_runewords}", generate_list_items(least_common_runewords)
            ).replace(
                "{least_popular_uniques}", generate_list_items(least_common_uniques)
            ).replace(
                "{least_popular_set_items}", generate_list_items(least_common_set_items)
            ).replace( 
                "{all_runewords}", generate_all_list_items(all_runewords, filtered_characters)
            ).replace(
                "{all_uniques}", generate_all_list_items(all_uniques, filtered_characters)
            ).replace(
                "{all_set}", generate_all_list_items(all_set, filtered_characters)
            ).replace(
                "{all_synth}", generate_synth_list_items(synth_counter, synth_users)
            ).replace(
                "{timeStamp}", timeStamp
            ).replace(
                "{synth_user_count}", str(synth_user_count)
            ).replace(
                "{all_crafted}", generate_crafted_list_items(crafted_counters, crafted_users)
            ).replace(
                "{craft_user_count}", str(craft_user_count)
            ).replace(
                "{synth_source_data}", generate_synth_source_list(synth_sources)
            ).replace(
                "{synth_source_user_count}", str(synth_source_user_count)
            ).replace(
                "{all_magic}", generate_magic_list_items(magic_counters, magic_users)
            ).replace(
                "{magic_user_count}", str(magic_user_count)
            ).replace(
                "{all_rare}", generate_rare_list_items(rare_counters, rare_users)
            ).replace(
                "{rare_user_count}", str(rare_user_count)
            ).replace(
                "{sorted_just_socketed_runes}", socketed_runes_html  # ✅ Correctly insert formatted HTML
            ).replace(
                "{sorted_just_socketed_excluding_runewords_runes}", socketed_excluding_runes_html
            ).replace(
                "{all_other_items}", other_items_html
            ).replace(
                "{fun_facts_html}", fun_facts_html
            ).replace(
                "{html_output}", html_output
            )

        # Save the report to a file
        output_file = f"pod-stats/{what_class}.html"
        with open(output_file, "w") as file:
            file.write(filled_html_content)

        print(f"Cluster analysis report saved to {output_file}")
    pass

    # ✅ Process all 7 classes
    for class_info in classes:
        generate_report(**class_info, all_characters=all_characters)

#MakeClassPages()

###############################################################
#
# Mercenary reporting
#




###############################################################
#
# Github sync
#
def GitHubSync():
    data_folder = "pod-stats"  # Change this to your folder name

    # Synchronize with GitHub
    def git_sync():
        try:
            # Navigate to the project directory
            os.chdir(data_folder)
            
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Commit changes
            subprocess.run(['git', 'commit', '-m', 'Automated commit message'], check=True)
            
            # Pull the latest changes from the remote repository to avoid conflicts
            subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
            
            # Push changes to the remote repository
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            print("GitHub sync completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"GitHub sync failed: {e}")

    # Specify the remote name you want to sync to
    remote = 'origin'  # Replace 'origin' with the desired remote name

    # Call the git_sync function with the specified remote
    git_sync()

