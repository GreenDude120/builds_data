#
#   V2
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


###############################################################
#
# Pull down character data
#
# Base URLs

def GetAllCharData(filter_mismatches=False):  # Add option to enable/disable filtering
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/"
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"
    sc_or_hc = "sc"

    classes = [
#        {"class_dir": "/barbarian", "what_class": "Barbarian", "api": "5/1"},
#        {"class_dir": "/druid", "what_class": "Druid", "api": "6/1"},
#        {"class_dir": "/amazon", "what_class": "Amazon", "api": "1/1"},
#        {"class_dir": "/assassin", "what_class": "Assassin", "api": "7/1"},
#        {"class_dir": "/necromancer", "what_class": "Necromancer", "api": "3/1"},
#        {"class_dir": "/paladin", "what_class": "Paladin", "api": "4/1"},
#        {"class_dir": "/sorceress", "what_class": "Sorceress", "api": "2/1"}
#        {"class_dir": "/ladder-top", "what_class": "top-200", "api": "0/1", "pages": 0},
        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/1", "pages": 0},
        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/2", "pages": 0},
        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/3", "pages": 0},
        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/4", "pages": 0},
        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/5", "pages": 0}
    ]

    if sc_or_hc == "sc":
        base_ladder_url += "0/"
    elif sc_or_hc == "hc":
        base_ladder_url += "1/"

    def validate_character_class(file_path, expected_class):
        """Deletes the JSON file if the character class does not match the expected class."""
        try:
            with open(file_path, "r") as file:
                char_data = json.load(file)

            actual_class = char_data.get("Class", "Unknown")
            if actual_class != expected_class:
                print(f"❌ Deleting {file_path} (Expected: {expected_class}, Found: {actual_class})")
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Error checking {file_path}: {e}")

    def generate_report(base_ladder_url, class_dir, what_class, api):
        ladder_url = base_ladder_url + api
        save_dir = sc_or_hc + class_dir

        os.makedirs(save_dir, exist_ok=True)

        response = requests.get(ladder_url)
        ladder_data = response.json()

        for character in ladder_data["ladder"]:
            char_name = character.get("charName", "unknown")
            char_id = character.get("id", None)

            if char_name == "unknown":
                char_name = f"unknown_{char_id or int(time.time() * 1000)}"

            character_response = requests.get(char_url.format(char_name=char_name))
            file_path = os.path.join(save_dir, f"{char_name}.json")

            with open(file_path, "w") as file:
                file.write(character_response.text)

            print(f"✅ Saved {char_name} to {file_path}")

            if filter_mismatches:
                validate_character_class(file_path, what_class)

    for cls in classes:
        generate_report(base_ladder_url, cls["class_dir"], cls["what_class"], cls["api"])

def GetClassCharData(filter_mismatches=True):  # Add option to enable/disable filtering
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/"
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"
    sc_or_hc = "sc"

    classes = [
        {"class_dir": "/barbarian", "what_class": "Barbarian", "api": "5/1"},
        {"class_dir": "/druid", "what_class": "Druid", "api": "6/1"},
        {"class_dir": "/amazon", "what_class": "Amazon", "api": "1/1"},
        {"class_dir": "/assassin", "what_class": "Assassin", "api": "7/1"},
        {"class_dir": "/necromancer", "what_class": "Necromancer", "api": "3/1"},
        {"class_dir": "/paladin", "what_class": "Paladin", "api": "4/1"},
        {"class_dir": "/sorceress", "what_class": "Sorceress", "api": "2/1"}
#        {"class_dir": "/ladder-top", "what_class": "top-200", "api": "0/1", "pages": 0},
#        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/1", "pages": 0},
#        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/2", "pages": 0},
#        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/3", "pages": 0},
#        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/4", "pages": 0},
#        {"class_dir": "/ladder-all", "what_class": "ladder1k", "api": "0/5", "pages": 0}
    ]

    if sc_or_hc == "sc":
        base_ladder_url += "0/"
    elif sc_or_hc == "hc":
        base_ladder_url += "1/"

    def validate_character_class(file_path, expected_class):
        """Deletes the JSON file if the character class does not match the expected class."""
        try:
            with open(file_path, "r") as file:
                char_data = json.load(file)

            actual_class = char_data.get("Class", "Unknown")
            if actual_class != expected_class:
                print(f"❌ Deleting {file_path} (Expected: {expected_class}, Found: {actual_class})")
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Error checking {file_path}: {e}")

    def generate_report(base_ladder_url, class_dir, what_class, api):
        ladder_url = base_ladder_url + api
        save_dir = sc_or_hc + class_dir

        os.makedirs(save_dir, exist_ok=True)

        response = requests.get(ladder_url)
        ladder_data = response.json()

        for character in ladder_data["ladder"]:
            char_name = character.get("charName", "unknown")
            char_id = character.get("id", None)

            if char_name == "unknown":
                char_name = f"unknown_{char_id or int(time.time() * 1000)}"

            character_response = requests.get(char_url.format(char_name=char_name))
            file_path = os.path.join(save_dir, f"{char_name}.json")

            with open(file_path, "w") as file:
                file.write(character_response.text)

            print(f"✅ Saved {char_name} to {file_path}")

            if filter_mismatches:
                validate_character_class(file_path, what_class)

    for cls in classes:
        generate_report(base_ladder_url, cls["class_dir"], cls["what_class"], cls["api"])


###############################################################
#
# Create home page
#
def MakeHome():


    # Define the folder containing the JSON files
    data_folder = "sc/ladder-all"
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
    rare_users = {category: {} for category in crafted_counters}  # Ensure all categories exist
    magic_users = {category: {} for category in crafted_counters}  # Ensure all categories exist

    all_characters = []
    sorted_just_socketed_runes = {}
    sorted_just_socketed_excluding_runewords_runes = {}
    all_other_items = {}


    
    # Function to process each JSON file
    def process_files_in_folder(folder):
        # Dictionary to store class counts
        class_counts = {}

        # Counters for runewords, uniques, and set items
        runeword_counter = Counter()
        unique_counter = Counter()
        set_counter = Counter()
        synth_counter = Counter()
        def categorize_worn_slot(worn_category, text_tag):
            if worn_category in ["sweapon1", "weapon1", "sweapon2", "weapon2"]:
                if text_tag == "Arrows":
                    return "Arrows"
                elif text_tag == "Bolts":
                    return "Bolts"
                else:
                    return "Weapons and Shields"
            
            worn_category_map = {
                "ring1": "Ring", "ring2": "RingsBody ",
                "body": "Armor",
                "gloves": "Gloves",
                "belt": "Belts",
                "helmet": "Helmets",
                "boots": "Boots",
                "amulet": "Amulets",
            }
            
            return worn_category_map.get(worn_category, "Other")  # Default to "Other"


        # Iterate through all JSON files in the folder
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                filepath = os.path.join(folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Attempt to parse the JSON
                    with open(filepath, 'r') as file:
                        char_data = json.load(file)
                        all_characters.append(char_data)  # Collect all character data

                        char_name = char_data.get("Name", "Unknown")
                        char_class = char_data.get("Class", "Unknown")
                        char_level = char_data.get("Stats", {}).get("Level", "Unknown")  # Correctly access level from Stats

                        # Process class data
                        char_class = char_data.get("Class")
                        if char_class:
                            class_counts[char_class] = class_counts.get(char_class, 0) + 1



                        # Process equipped items data
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
                                runeword_counter[item["Title"]] += 1
                                runeword_users.setdefault(item["Title"], []).append(character_info)

                            if item.get("QualityCode") == "q_unique":
                                unique_counter[item["Title"]] += 1
                                unique_users.setdefault(item["Title"], []).append(character_info)

                            if item.get("QualityCode") == "q_set":
                                set_counter[item["Title"]] += 1
                                set_users.setdefault(item["Title"], []).append(character_info)

                            if item.get("QualityCode") == "q_crafted":
                                crafted_counters[worn_category][item["Title"]] += 1
                                crafted_users.setdefault(worn_category, {}).setdefault(item["Title"], []).append(character_info)

                except (json.JSONDecodeError, KeyError, OSError) as e:
                    print(f"Error processing file {filepath}: {e}")
                    continue

        return class_counts, runeword_counter, unique_counter, set_counter, synth_counter, runeword_users, unique_users, set_users, synth_users, crafted_counters, crafted_users

    def process_files_in_folder_for_magic_rare(folder):
        magic_counters = {category: Counter() for category in crafted_counters}
        rare_counters = {category: Counter() for category in crafted_counters}
        magic_users = {category: {} for category in crafted_counters}
        rare_users = {category: {} for category in crafted_counters}
        def categorize_worn_slot(worn_category, text_tag):
            if worn_category in ["sweapon1", "weapon1", "sweapon2", "weapon2"]:
                if text_tag == "Arrows":
                    return "Arrows"
                elif text_tag == "Bolts":
                    return "Bolts"
                else:
                    return "Weapons and Shields"
            
            worn_category_map = {
                "ring1": "Ring", "ring2": "RingsBody ",
                "body": "Armor",
                "gloves": "Gloves",
                "belt": "Belts",
                "helmet": "Helmets",
                "boots": "Boots",
                "amulet": "Amulets",
            }
            
            return worn_category_map.get(worn_category, "Other")  # Default to "Other"

        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                filepath = os.path.join(folder, filename)
                try:
                    if os.path.getsize(filepath) == 0:
                        continue

                    with open(filepath, 'r') as file:
                        char_data = json.load(file)
                        char_name = char_data.get("Name", "Unknown")
                        char_class = char_data.get("Class", "Unknown")
                        char_level = char_data.get("Stats", {}).get("Level", "Unknown")

                        for item in char_data.get("Equipped", []):
                            worn_category = categorize_worn_slot(item.get("Worn", ""), item.get("TextTag", ""))
                            character_info = {"name": char_name, "class": char_class, "level": char_level}

                            if item.get("QualityCode") == "q_magic":
                                magic_counters[worn_category][item["Title"]] += 1
                                magic_users.setdefault(worn_category, {}).setdefault(item["Title"], []).append(character_info)

                            if item.get("QualityCode") == "q_rare":
                                rare_counters[worn_category][item["Title"]] += 1
                                rare_users.setdefault(worn_category, {}).setdefault(item["Title"], []).append(character_info)

                except (json.JSONDecodeError, KeyError, OSError) as e:
                    print(f"Error processing file {filepath}: {e}")
                    continue

        return magic_counters, magic_users, rare_counters, rare_users

    def GetSCFunFacts():
        # Define the folder containing character JSON files
        data_folder = "sc/ladder-all"

        # Function to load character data from JSON files
        def load_characters(folder):
            characters = []
            for filename in os.listdir(folder):
                if filename.endswith(".json"):
                    filepath = os.path.join(folder, filename)
                    try:
                        with open(filepath, "r") as file:
                            char_data = json.load(file)
                            characters.append(char_data)
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        print(f"Error reading {filename}: {e}")
            return characters

        # Load character data
        characters = load_characters(data_folder)

        # Extract alive characters
        alive_characters = [char for char in characters if not char.get("IsDead", True)]
        undead_count = len(alive_characters)

        # Function to format the alive characters list
        def GetTheLiving():
            return "".join(
                f"""
                <div class="character-info">
                    <div><strong>{char.get("Name", "Unknown")}</strong></div>
                    <div>Level {char.get("Stats", {}).get("Level", "N/A")} {char.get("Class", "Unknown")}</div>
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char.get("Name", "Unknown")}" target="_blank">
                            {char.get("Name", "Unknown")}'s Armory Page
                        </a>
                    </div>
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
    class_counts, runeword_counter, unique_counter, set_counter, synth_counter, runeword_users, unique_users, set_users, synth_users, crafted_counters, crafted_users = process_files_in_folder(data_folder)
    magic_counters, magic_users, rare_counters, rare_users = process_files_in_folder_for_magic_rare(data_folder)

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
        f"Class Distribution, Ladder Top 1,000\n\nAs of {timestamp}", 
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
                    <div><strong>{char["Name"]}</strong></div>
                    <div>Level {char["Stats"]["Level"]} {char["Class"]}</div>
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["Name"]}" target="_blank">
                            {char["Name"]}'s Armory Page
                        </a>
                    </div>
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
        print(f"Checking synth users for item: {item}")
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
                    <div><strong>{char["name"]}</strong></div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}'s Armory Page
                        </a>
                    </div>
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
                    <div><strong>{char["name"]}</strong></div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div>Used in: <strong>{char["synthesized_item"]}</strong></div>
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}'s Armory Page
                        </a>
                    </div>
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

                <strong>{source_item} (Properties found in {len(characters)} Synth Items)</strong>
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
                    <div><strong>{char["name"]}</strong></div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}'s Armory Page
                        </a>
                    </div>
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
                    <div><strong>{char["name"]}</strong></div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}'s Armory Page
                        </a>
                    </div>
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
                    <div><strong>{char["name"]}</strong></div>
                    <div>Level {char["level"]} {char["class"]}</div>
                    <div class="character-link">
                        <a href="https://pathofdiablo.com/p/armory/?name={char["name"]}" target="_blank">
                            {char["name"]}'s Armory Page
                        </a>
                    </div>
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

    def socket_html(sorted_runes, sorted_excluding_runes, all_other_items):
        def extract_element(item):
            if item.get('Title') == 'Rainbow Facet':
                element_types = ["fire", "cold", "lightning", "poison", "physical", "magic"]
                for element in element_types:
                    for prop in item.get('PropertyList', []):
                        if element in prop.lower():
                            return element.capitalize()
            return item.get('Title', 'Unknown')  # Use title if not "Rainbow Facet"

        rune_names = {
            "El Rune", "Eld Rune", "Tir Rune", "Nef Rune", "Eth Rune", "Ith Rune", "Tal Rune", "Ral Rune", "Ort Rune", "Thul Rune", "Amn Rune", "Sol Rune",
            "Shael Rune", "Dol Rune", "Hel Rune", "Io Rune", "Lum Rune", "Ko Rune", "Fal Rune", "Lem Rune", "Pul Rune", "Um Rune", "Mal Rune", "Ist Rune",
            "Gul Rune", "Vex Rune", "Ohm Rune", "Lo Rune", "Sur Rune", "Ber Rune", "Jah Rune", "Cham Rune", "Zod Rune"
        }

        def load_data(folder):
            all_items = [] # all items
            socketed_items = [] # items and what's in sockets
            items_excluding_runewords = [] # items and what's in sockets, minus runewords
            just_socketed = [] # just what's in sockets, not the socketed items themselves
            just_socketed_excluding_runewords = [] # just what's in sockets, not the socketed items themselves, minus runewords
            facet_elements = defaultdict(list)  # Dictionary to group items by their element
            shields_for_skulls = []
            weapons_for_skulls = []
            helmets_for_skulls = []
            armor_for_skulls = []
            jewel_counts = Counter()  # Count jewels by title and quality
            jewel_groupings = {"magic": [], "rare": []}  # To store Misc. Magic/Rare Jewels
            

            for filename in os.listdir(folder):
                if filename.endswith(".json"):
                    filepath = os.path.join(folder, filename)
                    try:
                        with open(filepath, 'r') as file:
                            char_data = json.load(file)
                            
                            for item in char_data.get('Equipped', []):

                                if item.get('Worn') == 'helmet':
                                    for socketed_item in item.get('Sockets', []):
                                        if socketed_item.get('Title') == "Perfect Skull":
                                            helmets_for_skulls.append(socketed_item)
                                elif item.get('Worn') == 'body':
                                    for socketed_item in item.get('Sockets', []):
                                        if socketed_item.get('Title') == "Perfect Skull":
                                            armor_for_skulls.append(socketed_item)
                                elif item.get('Worn') in ['weapon1', 'weapon2', 'sweapon1', 'sweapon2']:
                                    # Check if item has the "Block" property
                                    if any("Block" in prop for prop in item.get('PropertyList', [])):
                                        for socketed_item in item.get('Sockets', []):
                                            if socketed_item.get('Title') == "Perfect Skull":
                                                shields_for_skulls.append(socketed_item)
                                                print(filename)
                                    else:
                                        for socketed_item in item.get('Sockets', []):
                                            if socketed_item.get('Title') == "Perfect Skull":
                                                weapons_for_skulls.append(socketed_item)
        #                            if not("Block" in prop for prop in item.get('PropertyList', [])):
        #                                for socketed_item in item.get('Sockets', []):
        #                                    if socketed_item.get('Title') == "Perfect Skull":
        #                                        weapons_for_skulls.append(socketed_item)

                                if item.get('SocketCount', '0') > '0':  # Check if item has sockets
                                    all_items.append(item)
                                    if item.get('QualityCode') != 'q_runeword':  # Exclude runewords
                                        items_excluding_runewords.append(item)

                                    for socketed_item in item.get('Sockets', []):
                                        element = extract_element(socketed_item)
                                        socketed_items.append(socketed_item)
                                        facet_elements[element].append(socketed_item)
                                        
                                        just_socketed.append(socketed_item)
                                        
                                        # ✅ Extract QualityCode for categorization later
                                        quality_code = socketed_item.get('QualityCode', '')

                                        # ✅ Separate Magic and Rare Jewels
                                        if quality_code == "q_magic":
                                            socketed_item["GroupedTitle"] = "Misc. Magic Jewels"
                                        elif quality_code == "q_rare":
                                            socketed_item["GroupedTitle"] = "Misc. Rare Jewels"
                                        else:
                                            socketed_item["GroupedTitle"] = socketed_item.get("Title", "Unknown")  # Keep normal title

                                        if item.get('QualityCode') != 'q_runeword':
                                            items_excluding_runewords.append(socketed_item)
                                            just_socketed_excluding_runewords.append(socketed_item)
                                        
                                        if socketed_item.get('Title') == 'Rainbow Facet':
                                            facet_elements[element].append(socketed_item)


                    except (json.JSONDecodeError, KeyError, OSError) as e:
                        print(f"Error processing file {filepath}: {e}")
                        continue

            return all_items, socketed_items, items_excluding_runewords, just_socketed, just_socketed_excluding_runewords, facet_elements, shields_for_skulls, weapons_for_skulls, helmets_for_skulls, armor_for_skulls

        # Example usage
        folder = "sc/ladder-all"
        all_items, socketed_items, items_excluding_runewords, just_socketed, just_socketed_excluding_runewords, facet_elements, shields_for_skulls, weapons_for_skulls, helmets_for_skulls, armor_for_skulls = load_data(folder)

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
                    magic_jewel_counter["Misc. Magic Jewels"] += 1
                    if has_splash:
                        magic_jewel_counter["splash"] += 1
                elif quality == "q_rare":  # ✅ Track Rare Jewels with splash
                    has_splash = any("splash" in prop.lower() for prop in item.get("PropertyList", []))
                    rare_jewel_counter["Misc. Rare Jewels"] += 1
                    if has_splash:
                        rare_jewel_counter["splash"] += 1
                else:  # ✅ All other non-rune items
                    non_rune_counter[title] += 1

            return rune_counter, non_rune_counter, magic_jewel_counter, rare_jewel_counter, facet_counter

        just_socketed_runes, just_socketed_non_runes, just_socketed_magic, just_socketed_rare, just_socketed_facets = count_items_by_type(just_socketed)
        just_socketed_excluding_runewords_runes, just_socketed_excluding_runewords_non_runes, just_socketed_excluding_runewords_magic, just_socketed_excluding_runewords_rare, just_socketed_excluding_runewords_facets = count_items_by_type(just_socketed_excluding_runewords)

        # Use .most_common() to sort data in descending order
        sorted_just_socketed_runes = just_socketed_runes.most_common()
        sorted_just_socketed_excluding_runewords_runes = just_socketed_excluding_runewords_runes.most_common()

        # Combine non-runes, magic, rare, and facets into a single list
        all_other_items = [
            *(f"{item}: {count}" for item, count in just_socketed_excluding_runewords_non_runes.items()),
            f"Misc. Magic Jewels: {just_socketed_excluding_runewords_magic['Misc. Magic Jewels']} ({just_socketed_excluding_runewords_magic['splash']} include melee splash)",
            f"Misc. Rare Jewels: {just_socketed_excluding_runewords_rare['Misc. Rare Jewels']} ({just_socketed_excluding_runewords_rare['splash']} include melee splash)",
            *(f"Rainbow Facet ({element}): {counts['count']} ({counts['perfect']} are perfect)" for element, counts in just_socketed_excluding_runewords_facets.items())
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

    output_file = "all_mercenary_report.html"
    data_folder = "sc/ladder-all"

    def analyze_mercenaries(data_folder):
        # Dictionary to store mercenary counts and equipment
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))
        mercenary_names = Counter()  # ✅ Correctly using Counter()

        # Process each JSON file in the folder
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                filepath = os.path.join(data_folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Parse the JSON
                    with open(filepath, "r") as file:
                        char_data = json.load(file)

                        # Count mercenary types
                        mercenary = char_data.get("MercenaryType")
                        if mercenary:
                            readable_mercenary, _ = map_readable_names(mercenary, "")
                            mercenary_counts[readable_mercenary] += 1
                            
                            # ✅ Count mercenary names properly
                            merc_name = char_data.get("MercenaryName", "Unknown")
                            mercenary_names[merc_name] += 1
                            
                            # Count mercenary equipment titles by worn category
                            for item in char_data.get("MercenaryEquipped", []):
                                worn_category = item.get("Worn", "Unknown")
                                readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                title = item.get("Title", "Unknown")
                                mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                except json.JSONDecodeError:
                    continue
                except OSError:
                    continue

        return mercenary_counts, mercenary_equipment, mercenary_names  # ✅ Now mercenary_names is a Counter


    # Function to generate a report for all mercenaries
    def generate_mercenary_report(data_folder, output_file):
        data_folder = "sc/ladder-all"
        html_output = ""
        mercenary_counts, mercenary_equipment, mercenary_names = analyze_mercenaries(data_folder)
#        html_output = "<style> .column {float: left; width: 25%;} .row:after {content: ""; display: table; clear: both;} </style>"    
        # Generate HTML report
        html_output += "<p><h2>Mercenary Analysis and Popular Equipment</h2></p>"
        
        # Mercenary type counts
        html_output += "<p><h3>Mercenary Type Counts</h3></p>"
        html_output += "<ul>"
        for mercenary, count, in mercenary_counts.items():
            html_output += f"<li>{mercenary}: {count}</li>"
#            html_output += "<br><br><br><br><br><br>"
        html_output += "</ul>"

        # ✅ This now works!
        html_output += "<h3>Most Common Mercenary Names</h3><ul>"
        for name, count in mercenary_names.most_common(10):
            html_output += f"<li>{name}: {count}</li>"
        html_output += "</ul>"

        html_output += "<p><h3>Popular Equipment by Mercenary Type</h3></p"
        for mercenary, categories in mercenary_equipment.items():
            html_output += "<br>"
            html_output += f"<div class='row'><p><strong>{mercenary}</strong></p>"
            for worn_category, items in categories.items():
                html_output += f"<div class="+'merccolumn'+f"><strong>Most Common {worn_category}s:</strong>"
                html_output += "<ul>"
                top_items = items.most_common(10)  # Get the top 6 items in this category
                for title, count in top_items:
                    html_output += f"<li>{title}: {count}</li>"   
                html_output += "</ul></div>"
            html_output += "</div>"
#        html_output += "<br><br><br><br><br><br>"
        return html_output

    data_folder = "sc/ladder-all"
    html_output = generate_mercenary_report(data_folder,output_file)

    # Generating the HTML for the results
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        
<div class="main">
<br><br><br><br><br><br><br><br><br><br><br><br><br>
        <h1>PoD SOFTCORE STATS </h1>
        <!-- Embed the Plotly pie chart -->
    <!--     <h2>Pick a class below for more detail</h2>-->
    <!--     <iframe src="cluster_analysis_report.html"></iframe>  -->
        <div>
            <img src="charts/class_distribution.png">
        </div>
        <h3>HOME PAGE (THIS PAGE) STATS AND DATA ARE FROM THE TOP 1,000 LADDER CHARACTERS</h3>
        <h3>UNLESS STATED OTHERWISE, OTHER PAGE STATS AND DATA ARE FROM THE TOP 200 CHARACTERS OF THE RELEVANT CLASS OR CLASSES</h3>
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
</div>

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

    print("HTML file generated successfully.")



###############################################################
#
# Get dashing strike builds
#
# Item counts look funny
def GetDashers():
    import pandas as pd
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    import plotly.express as px
    import json
    import os
    from jinja2 import Template

    icons_folder = "icons"
    what_class = "Dashadin"
    howmany_skills = 4
    search_skill = "Dashing Strike"
    skill_threshold = 10

    # List of folders to search
    folders = [
        "sc/paladin"
    ]

    # List to store file paths of character data
    filtered_files = []
    # Function to process each JSON file

    # Function to process each JSON file
    def process_file(file_path, search_skill, skill_threshold):
        try:
            with open(file_path, 'r') as file:
                char_data = json.load(file)
                has_templars_might = False
                has_high_charge = False
                
                # Check for skills with more than the specified threshold
                for tab in char_data.get('SkillTabs', []):
                    for skill in tab.get('Skills', []):
                        if skill["Name"] == search_skill and skill["Level"] > skill_threshold:
                            has_high_charge = True
                            break

                if has_high_charge:
                    filtered_files.append(file_path)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {file_path}: {e}")
        except KeyError as e:
            print(f"Missing expected key in file {file_path}: {e}")

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

    # Function to search folders
    def search_folders(folders, search_skill, skill_threshold):
        for folder_path in folders:
            for foldername, subfolders, filenames in os.walk(folder_path):
                for filename in filenames:
                    if filename.endswith(".json"):
                        process_file(os.path.join(foldername, filename), search_skill, skill_threshold)

    # Perform the search
    search_folders(folders, search_skill, skill_threshold)

    # Load data function remains unchanged
    # Function to load and process data
    def load_data(filtered_files):
        all_data = []
        []
        for file_path in filtered_files:
            try:
                with open(file_path, 'r') as file:
                    char_data = json.load(file)
                    if 'SkillTabs' in char_data and 'Equipped' in char_data:
                            # Define color mappings for different QualityCodes
                            quality_colors = {
                                "q_runeword": "#edcd74",
                                "q_unique": "#edcd74",
                                "q_set": "#45a823",
#                                "q_magic": "lightblue",
                                "q_magic": "#7074c9",
                                "q_rare": "yellow",
                                "q_crafted": "orange"
                            }
                            skill_data = {}
                            skill_data['Name'] = char_data.get('Name', 'Unknown')
                            skill_data['Class'] = char_data.get('Class', 'Unknown')
    #                        what_class = skill_data['Class']
                            skill_data['Level'] = char_data.get('Stats', {}).get('Level', 'Unknown')  # Extract level from nested structure
                            
                            # Flatten skill data and sort in descending order by points
                            skills = []
                            for tab in char_data['SkillTabs']:
                                for skill in tab['Skills']:
                                    skill_name = skill['Name']
                                    skill_level = skill['Level']
                                    skill_data[skill_name] = skill_level
                                    skills.append((skill_name, skill_level))
                            # Sort skills in descending order
                            skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                            skill_data['Skills'] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])  # Combine skills into a comma-separated list

                            # Flatten equipment data and count titles
                            equipment_titles = {}
                            for item in char_data['Equipped']:
                                worn_category = item['Worn']
                                title = item.get('Title', 'Unknown')
                                quality_code = item.get('QualityCode', 'default')  # Get QualityCode (default if missing)
                                # Apply font color based on quality
                                color = quality_colors.get(quality_code, "white")  # Default to white if not in dict
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
                                elif worn_category in ['amulet']:
                                    worn_category = 'Amulet'
                                elif worn_category in ['ring']:
                                    worn_category = 'Ring'
                                if worn_category not in equipment_titles:
                                    equipment_titles[worn_category] = {}

                                if colored_title in equipment_titles[worn_category]:  # ✅ Only use `colored_title`
                                    equipment_titles[worn_category][colored_title] += 1
                                else:
                                    equipment_titles[worn_category][colored_title] = 1  # ✅ Start from 1, no x0
#                                print(equipment_titles)
                            skill_data['Equipment'] = ", ".join([f"{worn}: {title} x{count}" for worn, titles in equipment_titles.items() for title, count in titles.items()])  # Combine equipment into a comma-separated list
#                                skill_data['Equipment'] = ", ".join([f"{worn}: {title}" for worn, titles in equipment_titles.items() for title, count in titles.items()])  # Combine equipment into a comma-separated list
                            # ✅ Only keep "xN" if N > 1
                            skill_data['Equipment'] = ", ".join([
                                f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                                for worn, titles in equipment_titles.items() 
                                for title, count in titles.items()
                            ])
                            
                            mercenary_data = char_data.get("MercenaryType", "No mercenary")
                            readable_mercenary, _ = map_readable_names(mercenary_data)
                            mercenary_equipment = ", ".join(
                                [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                            ) if char_data.get("MercenaryEquipped") else "No equipment"

                            # Store the mercenary info for each character
                            skill_data['Mercenary'] = readable_mercenary
                            skill_data['MercenaryEquipment'] = mercenary_equipment
                            all_data.append(skill_data)
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
            print(all_data)    
        return pd.DataFrame(all_data).fillna(0)  # Fill missing skills with 0

    # Load the data
    df = load_data(filtered_files)

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

    </head>
    <body class="not-main">

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
        <div><strong>Name: {{ character['name'] }}</strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="character-link">
            <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}'s Armory
            </a>
        </div>
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

    def analyze_mercenaries(cluster_files):
        # Dictionary to store mercenary counts and equipment
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        # Process each JSON file in the folder
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                filepath = os.path.join(data_folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Parse the JSON
                    with open(filepath, "r") as file:
                        char_data = json.load(file)
                        mercenary = char_data.get("MercenaryType")
                        if mercenary:
                            # Count mercenary types
                            readable_mercenary, _ = map_readable_names(mercenary, "")
                            mercenary_counts[readable_mercenary] += 1
                            
                            # Count mercenary equipment titles by worn category
                            for item in char_data.get("MercenaryEquipped", []):
                                worn_category = item.get("Worn", "Unknown")
                                readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                title = item.get("Title", "Unknown")
                                mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                except json.JSONDecodeError:
                    continue
                except OSError:
                    continue

        return mercenary_counts, mercenary_equipment

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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(cluster_files)

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
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
                            <div class="skill-bar" style="width: {percent * 6}px; min-width: 300px;">
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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(data_folder)


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




###############################################################
#
# Get non Amazon bow users
#
# Item colors good to go
def GetNonZon():
    icons_folder = "icons"
    what_class = "Notazons"
    # Define the tags you're searching for
    # Define the tags you're searching for
    search_tags = ["Bolts", "Arrows"]
    howmany_clusters = 6
    howmany_skills = 4
    # List of folders to search
    folders = [
        "sc/barbarian",
        "sc/druid",
        "sc/assassin",
        "sc/necromancer",
        "sc/paladin",
        "sc/sorceress"
    ]

    # List to store file paths of character data
    filtered_files = []
    # Function to process each JSON file
    def process_file(file_path, search_tags):
        try:
            with open(file_path, 'r') as file:
                char_data = json.load(file)
                for item in char_data["Equipped"]:
                    if item["Tag"] in search_tags:
                        filtered_files.append(file_path)
                        break
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {file_path}: {e}")
        except KeyError as e:
            print(f"Missing expected key in file {file_path}: {e}")

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

    # Function to search folders
    def search_folders(folders, search_tags):
        for folder_path in folders:
            for foldername, subfolders, filenames in os.walk(folder_path):
                for filename in filenames:
                    if filename.endswith(".json"):
                        process_file(os.path.join(foldername, filename), search_tags)

    # Perform the search
    search_folders(folders, search_tags)

    # Load data function remains unchanged
    # Function to load and process data
    def load_data(filtered_files):
        all_data = []
        []
        for file_path in filtered_files:
            try:
                with open(file_path, 'r') as file:
                    char_data = json.load(file)
                    if 'SkillTabs' in char_data and 'Equipped' in char_data:
                            quality_colors = {
                                "q_runeword": "#edcd74",
                                "q_unique": "#edcd74",
                                "q_set": "#45a823",
##                                "q_magic": "lightblue",
                                "q_magic": "#7074c9",
                                "q_rare": "yellow",
                                "q_crafted": "orange"
                            }
                            skill_data = {}
                            skill_data['Name'] = char_data.get('Name', 'Unknown')
                            skill_data['Class'] = char_data.get('Class', 'Unknown')
    #                        what_class = skill_data['Class']
                            skill_data['Level'] = char_data.get('Stats', {}).get('Level', 'Unknown')  # Extract level from nested structure
                            
                            # Flatten skill data and sort in descending order by points
                            skills = []
                            for tab in char_data['SkillTabs']:
                                for skill in tab['Skills']:
                                    skill_name = skill['Name']
                                    skill_level = skill['Level']
                                    skill_data[skill_name] = skill_level
                                    skills.append((skill_name, skill_level))
                            # Sort skills in descending order
                            skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                            skill_data['Skills'] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])  # Combine skills into a comma-separated list

                            # Flatten equipment data and count titles
                            equipment_titles = {}
                            for item in char_data['Equipped']:
                                worn_category = item['Worn']
                                title = item.get('Title', 'Unknown')
                                quality_code = item.get('QualityCode', 'default')  # Get QualityCode (default if missing)
                                tag = item.get('Tag')
                                # Apply font color based on quality
                                color = quality_colors.get(quality_code, "white")  # Default to white if not in dict
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

                                # ✅ Group Magic/Rare/Crafted items as "Misc. Rare"
                                if quality_code in ["q_unique","q_runeword"]:
    #                                title = "Magic" + tag  # Standardized label
                                    colored_title = f"<span style='color: #edcd74;'>{title}</span>"  # Display color for rare items
                                if quality_code in ["q_set"]:
    #                                title = "Magic" + tag  # Standardized label
                                    colored_title = f"<span style='color: #45a823;'>{title}</span>"  # Display color for rare items
                                if quality_code in ["q_magic"]:
    #                                title = "Magic" + tag  # Standardized label
                                    colored_title = f"<span style='color: #7074c9;'>Magic {tag}</span>"  # Display color for rare items
                                if quality_code in ["q_rare",]:
    #                                title = "Rare" + tag  # Standardized label
                                    colored_title = f"<span style='color: yellow;'>Rare {tag}</span>"  # Display color for rare items
                                if quality_code in ["q_crafted"]:
    #                                title = "Crafted" + tag  # Standardized label
                                    colored_title = f"<span style='color: orange;'>Crafted {tag}</span>"  # Display color for rare items

                                if worn_category not in equipment_titles:
                                    equipment_titles[worn_category] = {}

                                if colored_title in equipment_titles[worn_category]:  # ✅ Only use `colored_title`
                                    equipment_titles[worn_category][colored_title] += 1
                                else:
                                    equipment_titles[worn_category][colored_title] = 1  # ✅ Start from 1, no x0

                            skill_data['Equipment'] = ", ".join([f"{worn}: {title} x{count}" for worn, titles in equipment_titles.items() for title, count in titles.items()])  # Combine equipment into a comma-separated list
#                                skill_data['Equipment'] = ", ".join([f"{worn}: {title}" for worn, titles in equipment_titles.items() for title, count in titles.items()])  # Combine equipment into a comma-separated list
                            # ✅ Only keep "xN" if N > 1
                            skill_data['Equipment'] = ", ".join([
                                f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                                for worn, titles in equipment_titles.items() 
                                for title, count in titles.items()
                            ])

                            mercenary_data = char_data.get("MercenaryType", "No mercenary")
                            readable_mercenary, _ = map_readable_names(mercenary_data)
                            mercenary_equipment = ", ".join(
                                [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                            ) if char_data.get("MercenaryEquipped") else "No equipment"

                            # Store the mercenary info for each character
                            skill_data['Mercenary'] = readable_mercenary
                            skill_data['MercenaryEquipment'] = mercenary_equipment
                            all_data.append(skill_data)
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
        return pd.DataFrame(all_data).fillna(0)  # Fill missing skills with 0


    # Load the data
    df = load_data(filtered_files)

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

    </head>
    <body class="not-main">

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
        <div><strong>Name: {{ character['name'] }}</strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="character-link">
            <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}'s Armory
            </a>
        </div>
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

        
    def analyze_mercenaries(cluster_files):
        # Dictionary to store mercenary counts and equipment
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        # Process each JSON file in the folder
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                filepath = os.path.join(data_folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Parse the JSON
                    with open(filepath, "r") as file:
                        char_data = json.load(file)
                        mercenary = char_data.get("MercenaryType")
                        if mercenary:
                            # Count mercenary types
                            readable_mercenary, _ = map_readable_names(mercenary, "")
                            mercenary_counts[readable_mercenary] += 1
                            
                            # Count mercenary equipment titles by worn category
                            for item in char_data.get("MercenaryEquipped", []):
                                worn_category = item.get("Worn", "Unknown")
                                readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                title = item.get("Title", "Unknown")
                                mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                except json.JSONDecodeError:
                    continue
                except OSError:
                    continue

        return mercenary_counts, mercenary_equipment



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


#            print("🔹 Original Equipment Counts:")
#            pp.pprint(equipment_counts)

        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary_counts, mercenary_equipment = analyze_mercenaries(cluster_files)

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
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
                            <div class="skill-bar" style="width: {percent * 6}px; min-width: 300px;">
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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(data_folder)
        


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

    # List of folders to search
    folders = [
        "sc/amazon",
        "sc/barbarian",
        "sc/druid",
        "sc/assassin",
        "sc/necromancer",
        "sc/paladin",
        "sc/sorceress"
    ]

    # List to store file paths of character data
    filtered_files = []

    # Function to process each JSON file
    def process_file(file_path, search_tags):
        try:
            with open(file_path, 'r') as file:
                char_data = json.load(file)
                for item in char_data["Equipped"]:
                    if item["Title"] in search_tags and item["QualityCode"] == "q_unique":
                        filtered_files.append(file_path)
                        break
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {file_path}: {e}")
        except KeyError as e:
            print(f"Missing expected key in file {file_path}: {e}")

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

    # Function to search folders
    def search_folders(folders, search_tags):
        for folder_path in folders:
            for foldername, subfolders, filenames in os.walk(folder_path):
                for filename in filenames:
                    if filename.endswith(".json"):
                        process_file(os.path.join(foldername, filename), search_tags)


    # Perform the search
    search_folders(folders, search_tags)

    # Function to load and process data
    # Function to load and process data
    def load_data(filtered_files):
        all_data = []
        print("🔍 Checking filtered_files:", filtered_files)  # Debug: List the files being processed

        for file_path in filtered_files:
            print(f"📂 Processing: {file_path}")  # Debug: Show file being read
            try:
                with open(file_path, 'r') as file:
                    char_data = json.load(file)
                    if 'SkillTabs' in char_data and 'Equipped' in char_data:
                        print(f"✅ Valid data in: {file_path}")  # Debug: Confirm valid file
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

            except Exception as e:
                print(f"❌ Error processing file {file_path}: {e}")

        return pd.DataFrame(all_data).fillna(0), equipment_titles, quality_colors, colored_title  # Return equipment_titles for further use

    # Example usage:
    df, equipment_titles, quality_colors, colored_title = load_data(filtered_files)

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

    </head>
    <body class="not-main">

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
        <div><strong>Name: {{ character['name'] }}</strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="character-link">
            <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}'s Armory
            </a>
        </div>
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

    def analyze_mercenaries(cluster_files):
        # Dictionary to store mercenary counts and equipment
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        # Process each JSON file in the folder
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                filepath = os.path.join(data_folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Parse the JSON
                    with open(filepath, "r") as file:
                        char_data = json.load(file)
                        mercenary = char_data.get("MercenaryType")
                        if mercenary:
                            # Count mercenary types
                            readable_mercenary, _ = map_readable_names(mercenary, "")
                            mercenary_counts[readable_mercenary] += 1
                            
                            # Count mercenary equipment titles by worn category
                            for item in char_data.get("MercenaryEquipped", []):
                                worn_category = item.get("Worn", "Unknown")
                                readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                title = item.get("Title", "Unknown")
                                mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                except json.JSONDecodeError:
                    continue
                except OSError:
                    continue

        return mercenary_counts, mercenary_equipment

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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(cluster_files)

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
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
            'label': f"{cluster_percentage:.2f}% of {what_class}'s Main Skills:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar" style="width: {percent * 6}px; min-width: 300px;">
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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(data_folder)


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

def GetBong():
    icons_folder = "icons"
    what_class = "Bong_and_Warpspear"
    search_tags = ["The Iron Jang Bong", "Warpspear"]
    howmany_clusters = 2
    howmany_skills = 4

    # List of folders to search
    folders = [
        "sc/amazon",
        "sc/barbarian",
        "sc/druid",
        "sc/assassin",
        "sc/necromancer",
        "sc/paladin",
        "sc/sorceress"
    ]

    # List to store file paths of character data
    filtered_files = []

    # Function to process each JSON file
    def process_file(file_path, search_tags):
        try:
            with open(file_path, 'r') as file:
                char_data = json.load(file)
                for item in char_data["Equipped"]:
                    if item["Title"] in search_tags:
                        filtered_files.append(file_path)
                        break
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {file_path}: {e}")
        except KeyError as e:
            print(f"Missing expected key in file {file_path}: {e}")

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

    # Function to search folders
    def search_folders(folders, search_tags):
        for folder_path in folders:
            for foldername, subfolders, filenames in os.walk(folder_path):
                for filename in filenames:
                    if filename.endswith(".json"):
                        process_file(os.path.join(foldername, filename), search_tags)

    # Perform the search
    search_folders(folders, search_tags)

    # Function to load and process data
    def load_data(filtered_files):
        all_data = []
        for file_path in filtered_files:
            try:
                with open(file_path, 'r') as file:
                    char_data = json.load(file)
                    if 'SkillTabs' in char_data and 'Equipped' in char_data:
                        quality_colors = {
                            "q_runeword": "#edcd74",
                            "q_unique": "#edcd74",
                            "q_set": "#45a823",
#                                "q_magic": "lightblue",
                            "q_magic": "#7074c9",
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

                        # Flatten equipment data and count titles
                        equipment_titles = {}
                        for item in char_data['Equipped']:
                            worn_category = item['Worn']
                            title = item.get('Title', 'Unknown')
                            quality_code = item.get('QualityCode', 'default')  # Get QualityCode (default if missing)
                            tag = item.get('Tag')
                            # Apply font color based on quality
                            color = quality_colors.get(quality_code, "white")  # Default to white if not in dict
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

                            # ✅ Group Magic/Rare/Crafted items as "Misc. Rare"
                            if quality_code in ["q_unique","q_runeword"]:
#                                title = "Magic" + tag  # Standardized label
                                title = f"<span style='color: #edcd74;'>{title}</span>"  # Display color for rare items
                            if quality_code in ["q_set"]:
#                                title = "Magic" + tag  # Standardized label
                                title = f"<span style='color: #45a823;'>{title}</span>"  # Display color for rare items
                            if quality_code in ["q_magic"]:
#                                title = "Magic" + tag  # Standardized label
                                title = f"<span style='color: #7074c9;'>Magic {tag}</span>"  # Display color for rare items
                            if quality_code in ["q_rare",]:
#                                title = "Rare" + tag  # Standardized label
                                title = f"<span style='color: yellow;'>Rare {tag}</span>"  # Display color for rare items
                            if quality_code in ["q_crafted"]:
#                                title = "Crafted" + tag  # Standardized label
                                title = f"<span style='color: orange;'>Crafted {tag}</span>"  # Display color for rare items

                            if worn_category not in equipment_titles:
                                equipment_titles[worn_category] = {}
                            if title not in equipment_titles[worn_category]:
                                equipment_titles[worn_category][title] = 0
                            equipment_titles[worn_category][title] += 1

                        skill_data['Equipment'] = ", ".join([f"{worn}: {title} x{count}" for worn, titles in equipment_titles.items() for title, count in titles.items()])

                        # Add item presence information
                        for tag in search_tags:
                            skill_data[tag] = 1 if any(item.get('Title') == tag for item in char_data['Equipped']) else 0

                        mercenary_data = char_data.get("MercenaryType", "No mercenary")
                        readable_mercenary, _ = map_readable_names(mercenary_data)
                        mercenary_equipment = ", ".join(
                            [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                        ) if char_data.get("MercenaryEquipped") else "No equipment"

                        # Store the mercenary info for each character
                        skill_data['Mercenary'] = readable_mercenary
                        skill_data['MercenaryEquipment'] = mercenary_equipment
                        # Track presence of specific unique items
                        for tag in search_tags:
                            skill_data[tag] = 1 if any(item.get('Title') == tag for item in char_data['Equipped']) else 0

                        all_data.append(skill_data)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
        return pd.DataFrame(all_data).fillna(0)

    # Load the data
    df = load_data(filtered_files)

    # Define skill columns (exclude non-skill columns)
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment'] + search_tags]
#    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment'] + search_tags]

   # Create clusters based on item presence
    df["Cluster"] = df.apply(
        lambda row: "The Iron Jang Bong" if row.get("The Iron Jang Bong", 0) == 1 
        else ("Warpspear" if row.get("Warpspear", 0) == 1 else "Other"), axis=1
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

    </head>
    <body class="not-main">

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
        <div><strong>Name: {{ character['name'] }}</strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="character-link">
            <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}'s Armory
            </a>
        </div>
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

    def analyze_mercenaries(cluster_files):
        # Dictionary to store mercenary counts and equipment
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        # Process each JSON file in the folder
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                filepath = os.path.join(data_folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Parse the JSON
                    with open(filepath, "r") as file:
                        char_data = json.load(file)
                        mercenary = char_data.get("MercenaryType")
                        if mercenary:
                            # Count mercenary types
                            readable_mercenary, _ = map_readable_names(mercenary, "")
                            mercenary_counts[readable_mercenary] += 1
                            
                            # Count mercenary equipment titles by worn category
                            for item in char_data.get("MercenaryEquipped", []):
                                worn_category = item.get("Worn", "Unknown")
                                readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                title = item.get("Title", "Unknown")
                                mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                except json.JSONDecodeError:
                    continue
                except OSError:
                    continue

        return mercenary_counts, mercenary_equipment

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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(cluster_files)

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
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
            



        clusters[cluster] = {
#            'label': f"{cluster} users:<br>" + "<br>".join([f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> {skill} {percent:.2f}% ({int(avg*character_count)})" for skill, avg, percent in top_skills_with_avg_and_percent[cluster]]),  # Use top skills with average points and percentages as cluster label        'character_count': character_count,  # Add character count to the data
            'label': f"{cluster_percentage:.2f}% of {what_class}'s Main Skills:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar" style="width: {percent * 6}px; min-width: 300px;">
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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(data_folder)


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



###############################################################
#
# Chargers????
#
# Define search criteria
def GetChargers():
    import pandas as pd
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    import plotly.express as px
    import json
    import os
    from jinja2 import Template

    icons_folder = "icons"
    what_class = "Charge"
    howmany_clusters = 5
    howmany_skills = 4
    # Define the tags and item names you're searching for
    #search_tags = ["Bolts", "Arrows"]
    search_item = "Templar's Might"
    search_skill = "Charge"
    skill_threshold = 3

    # List of folders to search
    folders = [
        "sc/barbarian",
        "sc/druid",
        "sc/assassin",
        "sc/necromancer",
        "sc/paladin",
        "sc/sorceress",
        "sc/amazon"
    ]
    

    # List to store file paths of character data
    filtered_files = []
    # Function to process each JSON file

    # Function to process each JSON file
    def process_file(file_path, search_item, search_skill, skill_threshold):
        try:
            with open(file_path, 'r') as file:
                char_data = json.load(file)
                has_templars_might = False
                has_high_charge = False
                
                # Check for items with the specified tag or name
                for item in char_data["Equipped"]:
                    if item["Title"] == search_item:
                        has_templars_might = True
                        break
                
                # Check for skills with more than the specified threshold
                for tab in char_data.get('SkillTabs', []):
                    for skill in tab.get('Skills', []):
                        if skill["Name"] == search_skill and skill["Level"] > skill_threshold:
                            has_high_charge = True
                            break

                if has_templars_might or has_high_charge:
                    filtered_files.append(file_path)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {file_path}: {e}")
        except KeyError as e:
            print(f"Missing expected key in file {file_path}: {e}")

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

    # Function to search folders
    def search_folders(folders, search_item, search_skill, skill_threshold):
        for folder_path in folders:
            for foldername, subfolders, filenames in os.walk(folder_path):
                for filename in filenames:
                    if filename.endswith(".json"):
                        process_file(os.path.join(foldername, filename), search_item, search_skill, skill_threshold)

    # Perform the search
    search_folders(folders, search_item, search_skill, skill_threshold)

    # Load data function remains unchanged
    # Function to load and process data
    def load_data(filtered_files):
        all_data = []
        []
        for file_path in filtered_files:
            try:
                with open(file_path, 'r') as file:
                    char_data = json.load(file)
                    if 'SkillTabs' in char_data and 'Equipped' in char_data:
                            quality_colors = {
                                "q_runeword": "#edcd74",
                                "q_unique": "#edcd74",
                                "q_set": "#45a823",
#                                "q_magic": "lightblue",
                                "q_magic": "#7074c9",
                                "q_rare": "yellow",
                                "q_crafted": "orange"
                            }
                            skill_data = {}
                            skill_data['Name'] = char_data.get('Name', 'Unknown')
                            skill_data['Class'] = char_data.get('Class', 'Unknown')
    #                        what_class = skill_data['Class']
                            skill_data['Level'] = char_data.get('Stats', {}).get('Level', 'Unknown')  # Extract level from nested structure
                            
                            # Flatten skill data and sort in descending order by points
                            skills = []
                            for tab in char_data['SkillTabs']:
                                for skill in tab['Skills']:
                                    skill_name = skill['Name']
                                    skill_level = skill['Level']
                                    skill_data[skill_name] = skill_level
                                    skills.append((skill_name, skill_level))
                            # Sort skills in descending order
                            skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
                            skill_data['Skills'] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])  # Combine skills into a comma-separated list

                            # Flatten equipment data and count titles
                            equipment_titles = {}
                            for item in char_data['Equipped']:
                                worn_category = item['Worn']
                                title = item.get('Title', 'Unknown')
                                quality_code = item.get('QualityCode', 'default')  # Get QualityCode (default if missing)
                                tag = item.get('Tag')
                                # Apply font color based on quality
                                color = quality_colors.get(quality_code, "white")  # Default to white if not in dict
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
                                elif worn_category in ['amulet']:
                                    worn_category = 'Amulet'
                                elif worn_category in ['ring']:
                                    worn_category = 'Ring'

                                # ✅ Group Magic/Rare/Crafted items as "Misc. Rare"
                                if quality_code in ["q_unique","q_runeword"]:
    #                                title = "Magic" + tag  # Standardized label
                                    colored_title = f"<span style='color: #edcd74;'>{title}</span>"  # Display color for rare items
                                if quality_code in ["q_set"]:
    #                                title = "Magic" + tag  # Standardized label
                                    colored_title = f"<span style='color: #45a823;'>{title}</span>"  # Display color for rare items
                                if quality_code in ["q_magic"]:
    #                                title = "Magic" + tag  # Standardized label
                                    colored_title = f"<span style='color: #7074c9;'>Magic {tag}</span>"  # Display color for rare items
                                if quality_code in ["q_rare",]:
    #                                title = "Rare" + tag  # Standardized label
                                    colored_title = f"<span style='color: yellow;'>Rare {tag}</span>"  # Display color for rare items
                                if quality_code in ["q_crafted"]:
    #                                title = "Crafted" + tag  # Standardized label
                                    colored_title = f"<span style='color: orange;'>Crafted {tag}</span>"  # Display color for rare items


                                if worn_category not in equipment_titles:
                                    equipment_titles[worn_category] = {}

                                if colored_title in equipment_titles[worn_category]:  # ✅ Only use `colored_title`
                                    equipment_titles[worn_category][colored_title] += 1
                                else:
                                    equipment_titles[worn_category][colored_title] = 1  # ✅ Start from 1, no x0

                            skill_data['Equipment'] = ", ".join([f"{worn}: {title} x{count}" for worn, titles in equipment_titles.items() for title, count in titles.items()])  # Combine equipment into a comma-separated list
                            
                            mercenary_data = char_data.get("MercenaryType", "No mercenary")
                            readable_mercenary, _ = map_readable_names(mercenary_data)
                            mercenary_equipment = ", ".join(
                                [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                            ) if char_data.get("MercenaryEquipped") else "No equipment"

                            # Store the mercenary info for each character
                            skill_data['Mercenary'] = readable_mercenary
                            skill_data['MercenaryEquipment'] = mercenary_equipment
                            all_data.append(skill_data)
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
        return pd.DataFrame(all_data).fillna(0)  # Fill missing skills with 0


    # Load the data
    df = load_data(filtered_files)

    # Define skill columns (exclude non-skill columns)
    skill_columns = [col for col in df.columns if col not in ['Name', 'Class', 'Level', 'Skills', 'Equipment', 'Mercenary', 'MercenaryEquipment']]

    # Perform PCA
    pca = PCA(n_components=2)
    reduced_data = pca.fit_transform(df[skill_columns])

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

    </head>
    <body class="not-main">

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
        <div><strong>Name: {{ character['name'] }}</strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="character-link">
            <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}'s Armory
            </a>
        </div>
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

    def analyze_mercenaries(cluster_files):
        # Dictionary to store mercenary counts and equipment
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        # Process each JSON file in the folder
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                filepath = os.path.join(data_folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Parse the JSON
                    with open(filepath, "r") as file:
                        char_data = json.load(file)
                        mercenary = char_data.get("MercenaryType")
                        if mercenary:
                            # Count mercenary types
                            readable_mercenary, _ = map_readable_names(mercenary, "")
                            mercenary_counts[readable_mercenary] += 1
                            
                            # Count mercenary equipment titles by worn category
                            for item in char_data.get("MercenaryEquipped", []):
                                worn_category = item.get("Worn", "Unknown")
                                readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                title = item.get("Title", "Unknown")
                                mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                except json.JSONDecodeError:
                    continue
                except OSError:
                    continue

        return mercenary_counts, mercenary_equipment

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
                if item:  # Ensure item is not empty
                    worn, title_count = item.split(": ", 1)
                    title, count = title_count.split(" x")
                    count = int(count)
                    if worn not in equipment_counts:
                        equipment_counts[worn] = {}
                    if title not in equipment_counts[worn]:
                        equipment_counts[worn][title] = 0
                    equipment_counts[worn][title] += count

        # Extract character file paths for this cluster
        cluster_files = [f"{row.Class.lower()}/{row.Name}.json" for row in sorted_group.itertuples()]
        cluster_files = [path for path in cluster_files if os.path.exists(path)]  # Filter only existing files

        # Get mercenary data **just for this cluster**
        mercenary_counts, mercenary_equipment = analyze_mercenaries(cluster_files)

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
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
                            <div class="skill-bar" style="width: {percent * 6}px; min-width: 300px;">
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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(data_folder)


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



###############################################################
#
# Get chars with 2 or more offensive aura granting items
#
def GetOffensiveAuraItemsEquipped():
    icons_folder = "icons"
    what_class = "2AuraItems"
    search_tags = ["Dream", "Dragon", "Hand of Justice", "Doom", "Todesfaelle Flamme", "Azurewrath"]
    search_tags2 = ["Unique"]
    howmany_clusters = 6
    howmany_skills = 4

    # List of folders to search
    folders = [
        "sc/amazon",
        "sc/barbarian",
        "sc/druid",
        "sc/assassin",
        "sc/necromancer",
        "sc/paladin",
        "sc/sorceress"
    ]

    # List to store file paths of character data
    filtered_files = []

    # Function to process each JSON file
    def process_file(file_path, search_tags):
        try:
            with open(file_path, 'r') as file:
                char_data = json.load(file)
                tag_count = 0  # Initialize a counter for search tags
                for item in char_data["Equipped"]:
                    if item["Title"] in search_tags:
                        tag_count += 1
                    if tag_count >= 2:
                        filtered_files.append(file_path)
                        break
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {file_path}: {e}")
        except KeyError as e:
            print(f"Missing expected key in file {file_path}: {e}")

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

    # Function to search folders
    def search_folders(folders, search_tags):
        for folder_path in folders:
            for foldername, subfolders, filenames in os.walk(folder_path):
                for filename in filenames:
                    if filename.endswith(".json"):
                        process_file(os.path.join(foldername, filename), search_tags)


    # Perform the search
    search_folders(folders, search_tags)

    # Function to load and process data
    # Function to load and process data
    def load_data(filtered_files):
        all_data = []
        for file_path in filtered_files:
            try:
                with open(file_path, 'r') as file:
                    char_data = json.load(file)
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
                            quality = item.get('Quality', 'Unknown')
                            quality_code = item.get('QualityCode', 'Unknown')
#                            title_tag = f"{title} {worn_category}"  # Combine Title and Tag
                            if worn_category in ['ring1', 'ring2']:
                                worn_category = 'ring'
                            elif title == "Dream" and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                                worn_category = 'Sheild'
                            elif title == "Dragon" and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                                worn_category = 'Sheild'
#                            elif title == ("Hand of Justice" or "Doom" or "Todesfaelle Flamme") and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
#                                worn_category = 'Weapon'
                            elif title == "Hand of Justice" and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                                worn_category = 'Weapon'
                            elif title == "Doom" and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                                worn_category = 'Weapon'
                            elif title == "Todesfaelle Flamme" and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                                worn_category = 'Weapon'
                            elif title == "Azurewrath" and worn_category in ['sweapon1', 'weapon1', 'sweapon2', 'weapon2']:
                                worn_category = 'Weapon'
                            elif worn_category in ['sweapon1', 'weapon1']:
                                worn_category = 'Left hand'
                            elif worn_category in ['sweapon2', 'weapon2']:
                                worn_category = 'Offhand'
                            elif worn_category in ['body']:
                                worn_category = 'Armor'
                            elif worn_category in ['helmet']:
                                worn_category = 'Helmet'

                            if quality_code in ["q_magic"]:
#                                title = "Magic" + tag  # Standardized label
                                title = f"<span style='color: #7074c9;'>Magic {tag}</span>"  # Display color for rare items
                            if quality_code in ["q_rare",]:
#                                title = "Rare" + tag  # Standardized label
                                title = f"<span style='color: yellow;'>Rare {tag}</span>"  # Display color for rare items
                            if quality_code in ["q_crafted"]:
#                                title = "Crafted" + tag  # Standardized label
                                title = f"<span style='color: orange;'>Crafted {tag}</span>"  # Display color for rare items

                            if worn_category not in equipment_titles:
                                equipment_titles[worn_category] = {}
                            if title not in equipment_titles[worn_category]:
                                equipment_titles[worn_category][title] = 0
                            equipment_titles[worn_category][title] += 1
#                            if quality == "Unique":  # Ensure only Unique quality items are counted
#                                equipment_titles[worn_category][title_tag] += 1

                        skill_data['Equipment'] = ", ".join([f"{worn}: {title_tag} x{count}" for worn, titles in equipment_titles.items() for title_tag, count in titles.items()])

                        # Add item presence information
                        for tag in search_tags:
                            skill_data[tag] = 1 if any(item.get('Tag') == tag and item.get('Quality') == 'Unique' for item in char_data['Equipped']) else 0

                        mercenary_data = char_data.get("MercenaryType", "No mercenary")
                        readable_mercenary, _ = map_readable_names(mercenary_data)
                        mercenary_equipment = ", ".join(
                            [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                        ) if char_data.get("MercenaryEquipped") else "No equipment"

                        # Store the mercenary info for each character
                        skill_data['Mercenary'] = readable_mercenary
                        skill_data['MercenaryEquipment'] = mercenary_equipment
                        all_data.append(skill_data)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
        return pd.DataFrame(all_data).fillna(0)

    # Load the data
    df = load_data(filtered_files)

    filtered_file_count = len(filtered_files)
    print(f"Number of filtered files: {filtered_file_count}")
    print("Filtered files:", filtered_files)

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

    </head>
    <body class="not-main">

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
        <div><strong>Name: {{ character['name'] }}</strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="character-link">
            <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}'s Armory
            </a>
        </div>
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

    def analyze_mercenaries(cluster_files):
        # Dictionary to store mercenary counts and equipment
        mercenary_counts = Counter()
        mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

        # Process each JSON file in the folder
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                filepath = os.path.join(data_folder, filename)
                try:
                    # Check if the file is empty
                    if os.path.getsize(filepath) == 0:
                        continue

                    # Parse the JSON
                    with open(filepath, "r") as file:
                        char_data = json.load(file)
                        mercenary = char_data.get("MercenaryType")
                        if mercenary:
                            # Count mercenary types
                            readable_mercenary, _ = map_readable_names(mercenary, "")
                            mercenary_counts[readable_mercenary] += 1
                            
                            # Count mercenary equipment titles by worn category
                            for item in char_data.get("MercenaryEquipped", []):
                                worn_category = item.get("Worn", "Unknown")
                                readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                title = item.get("Title", "Unknown")
                                mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                except json.JSONDecodeError:
                    continue
                except OSError:
                    continue

        return mercenary_counts, mercenary_equipment

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
        mercenary_counts, mercenary_equipment = analyze_mercenaries(cluster_files)

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
                    f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
            'label': f"{cluster_percentage:.2f}% of {what_class}'s Main Skills:<br>" + "".join([
                f"""
                <div class="skillbar-container">
                    <div class="skill-row">
                        <img src="{icons_folder}/{skill}.png" alt="{skill}" class="skill-icon">
                        <div class="skill-bar-container">
                            <div class="skill-bar" style="width: {percent * 6}px; min-width: 300px;">
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
            'filtered_file_count': filtered_file_count,
            
        }
        mercenary_counts, mercenary_equipment = analyze_mercenaries(data_folder)


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
    html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, filtered_file_count=filtered_file_count, timeStamp=timeStamp)  # Pass sorted clusters to the template

    # Save the report to a file
    output_file = f"pod-stats/{what_class}.html"
    with open(output_file, "w") as file:
        file.write(html_content)

    print(f"Cluster analysis report saved to {output_file}")





###############################################################
#
# Generate class html's
#
def MakeClassPages():
    classes = [
        {"data_folder": "sc/barbarian", "what_class": "Barbarian", "howmany_clusters": 13, "howmany_skills": 5}, # orig:8 4, silhouettes says 13, gap says 13
        {"data_folder": "sc/druid", "what_class": "Druid", "howmany_clusters": 14, "howmany_skills": 5}, # orig:6 3, silhouettes says 8, gap says 14
        {"data_folder": "sc/amazon", "what_class": "Amazon", "howmany_clusters": 13, "howmany_skills": 5}, # orig:6 4, silhouettes says 4, gap says 13
        {"data_folder": "sc/assassin", "what_class": "Assassin", "howmany_clusters": 14, "howmany_skills": 5}, # orig:7 4, silhouettes says 5, gap says 14
        {"data_folder": "sc/necromancer", "what_class": "Necromancer", "howmany_clusters": 14, "howmany_skills": 5}, # orig:3 4, silhouettes says 2, gap says 14
        {"data_folder": "sc/paladin", "what_class": "Paladin", "howmany_clusters": 12, "howmany_skills": 5}, # orig:7 3, silhouettes says 4, gap says 12
        {"data_folder": "sc/sorceress", "what_class": "Sorceress", "howmany_clusters": 14, "howmany_skills": 5} # orig:13 5, silhouettes says 10, gap says 14
    ]
    icons_folder = "icons"

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


    def generate_report(data_folder, what_class, howmany_clusters, howmany_skills):


    #data_folder = "pally"  # Change this to your folder name
    #what_class = "Paladin"
    #howmany_clusters = 7
    #howmany_skills = 3

        # Load data function remains unchanged
        # Function to load and process data
        def load_data(data_folder):
            all_data = []
            for filename in os.listdir(data_folder):
                if filename.endswith(".json"):
                    file_path = os.path.join(data_folder, filename)
                    try:
                        with open(file_path, 'r') as file:
                            char_data = json.load(file)
                            if 'SkillTabs' in char_data and 'Equipped' in char_data:
                                # Define color mappings for different QualityCodes
                                quality_colors = {
                                    "q_runeword": "#edcd74",
                                    "q_unique": "#edcd74",
                                    "q_set": "#45a823",
    #                                "q_magic": "lightblue",
                                "q_magic": "#7074c9",
                                    "q_rare": "yellow",
                                    "q_crafted": "orange"
                                }
                                skill_data = {}
                                skill_data['Name'] = char_data.get('Name', 'Unknown')
                                skill_data['Class'] = char_data.get('Class', 'Unknown')
                                skill_data['Level'] = char_data.get('Stats', {}).get('Level', 'Unknown')  # Extract level from nested structure
                                
                                # Flatten skill data and sort in descending order by points
                                skills = []
                                for tab in char_data['SkillTabs']:
                                    for skill in tab['Skills']:
                                        skill_name = skill['Name']
                                        skill_level = skill['Level']
                                        skill_data[skill_name] = skill_level
                                        skills.append((skill_name, skill_level))
                                # Sort skills in descending order
                                skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
#                                skill_data['Skills'] = ", ".join([f"{name}:{level}" for name, level in skills_sorted])  # Combine skills into a comma-separated list
                                skill_data['Skills'] = ", ".join([f"<img src='{icons_folder}/{name}.png' alt='{name}' width='20' height='20'> {name}:{level}" for name, level in skills_sorted])  # Combine skills into a comma-separated list

                                # Flatten equipment data and count titles
                                equipment_titles = {}
                                for item in char_data['Equipped']:
                                    worn_category = item['Worn']
                                    title = item.get('Title', 'Unknown')
                                    quality_code = item.get('QualityCode', 'default')  # Get QualityCode (default if missing)
                                    tag = item.get('Tag')
                                    # Apply font color based on quality
                                    color = quality_colors.get(quality_code, "white")  # Default to white if not in dict
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


                                    # ✅ Group Magic/Rare/Crafted items as "Misc. Rare"
                                    if quality_code in ["q_magic"]:
                                        title = "Magic" + tag  # Standardized label
                                        colored_title = f"<span style='color: #7074c9;'>Magic {tag}</span>"  # Display color for rare items
                                    if quality_code in ["q_rare",]:
                                        title = "Rare" + tag  # Standardized label
                                        colored_title = f"<span style='color: yellow;'>Rare {tag}</span>"  # Display color for rare items
                                    if quality_code in ["q_crafted"]:
                                        title = "Crafted" + tag  # Standardized label
                                        colored_title = f"<span style='color: orange;'>Crafted {tag}</span>"  # Display color for rare items

                                    if worn_category not in equipment_titles:
                                        equipment_titles[worn_category] = {}

                                    if colored_title in equipment_titles[worn_category]:  # ✅ Only use `colored_title`
                                        equipment_titles[worn_category][colored_title] += 1
                                    else:
                                        equipment_titles[worn_category][colored_title] = 1  # ✅ Start from 1, no x0
#                                print(equipment_titles)
                                skill_data['Equipment'] = ", ".join([f"{worn}: {title} x{count}" for worn, titles in equipment_titles.items() for title, count in titles.items()])  # Combine equipment into a comma-separated list
#                                skill_data['Equipment'] = ", ".join([f"{worn}: {title}" for worn, titles in equipment_titles.items() for title, count in titles.items()])  # Combine equipment into a comma-separated list
                                # ✅ Only keep "xN" if N > 1
                                skill_data['Equipment'] = ", ".join([
                                    f"{worn}: {title} x{count}" if count > 1 else f"{worn}: {title}"
                                    for worn, titles in equipment_titles.items() 
                                    for title, count in titles.items()
                                ])
                                
                                mercenary_data = char_data.get("MercenaryType", "No mercenary")
                                readable_mercenary, _ = map_readable_names(mercenary_data)
                                mercenary_equipment = ", ".join(
                                    [item.get("Title", "Unknown") for item in char_data.get("MercenaryEquipped", [])]
                                ) if char_data.get("MercenaryEquipped") else "No equipment"

                                # Store the mercenary info for each character
                                skill_data['Mercenary'] = readable_mercenary
                                skill_data['MercenaryEquipment'] = mercenary_equipment
                                all_data.append(skill_data)
                    except Exception as e:
                        print(f"Error processing file {filename}: {e}")
            return pd.DataFrame(all_data).fillna(0)  # Fill missing skills with 0


       
        # Load the data
        df = load_data(data_folder)

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

        def GetSCFunFacts():
            # Define the folder containing character JSON files
            #data_folder = "sc/ladder-all"

            # Function to load character data from JSON files
            def load_characters(data_folder):
                characters = []
                for filename in os.listdir(data_folder):
                    if filename.endswith(".json"):
                        filepath = os.path.join(data_folder, filename)
                        try:
                            with open(filepath, "r") as file:
                                char_data = json.load(file)
                                characters.append(char_data)
                        except (json.JSONDecodeError, FileNotFoundError) as e:
                            print(f"Error reading {filename}: {e}")
                return characters

            # Load character data
            characters = load_characters(data_folder)

            # Extract alive characters
            alive_characters = [char for char in characters if not char.get("IsDead", True)]
            undead_count = len(alive_characters)

            # Function to format the alive characters list
            def GetTheLiving():
                return "".join(
                    f"""
                    <div class="character-info">
                        <div><strong>{char.get("Name", "Unknown")}</strong></div>
                        <div>Level {char.get("Stats", {}).get("Level", "N/A")} {char.get("Class", "Unknown")}</div>
                        <div class="character-link">
                            <a href="https://pathofdiablo.com/p/armory/?name={char.get("Name", "Unknown")}" target="_blank">
                                {char.get("Name", "Unknown")}'s Armory Page
                            </a>
                        </div>
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
            <h3>{what_class} Fun Facts</h3>
                <h3>{undead_count} Characters in the {what_class} top {character_count} have not died</h3>
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
                    <h3>Top 5 {what_class}'s with the most Strength:</h3>
                    <ul>{top_strength}</ul>
                </div>
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the most Dexterity:</h3>
                    <ul>{top_dexterity}</ul>
                </div>
            </div>

            <!-- Vitality & Energy Row -->
            <div class="fun-facts-row">
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the most Vitality:</h3>
                    <ul>{top_vitality}</ul>
                </div>
                <div class="fun-facts-column">
                    <h3>Top 5 {what_class}'s with the most Energy:</h3>
                    <ul>{top_energy}</ul>
                </div>
            </div>

            <!-- Life & Mana Row -->
            <div class="fun-facts-row">
                <div class="fun-facts-column">
                    <h3>The 5 {what_class}'s with the Most Life:</h3>
                    <ul>{top_life}</ul>
                    <p><strong>Average Life:</strong> {average_life:.2f}</p>
                </div>
                <div class="fun-facts-column">
                    <h3>The 5 {what_class}'s with the Most Mana:</h3>
                    <ul>{top_mana}</ul>
                    <p><strong>Average Mana:</strong> {average_mana:.2f}</p>
                </div>
            </div>

            <!-- Magic Find & Gold Find Row -->
            <div class="fun-facts-row">
                <div class="fun-facts-column">
                    <h3>The 5 {what_class}'s with the Most Magic Find:</h3>
                    <ul>{top_magic_find}</ul>
                    <p><strong>Average Magic Find:</strong> {average_mf:.2f}</p>
                </div>
                <div class="fun-facts-column">
                    <h3>The 5 {what_class}'s with the Most Gold Find:</h3>
                    <ul>{top_gold_find}</ul>
                    <p><strong>Average Gold Find:</strong> {average_gf:.2f}</p>
                </div>
            </div>
            """

            return fun_facts_html

        # Generate fun facts
        fun_facts_html = GetSCFunFacts()


        # Updated HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ what_class }} Analysis Report</title>
        <link rel="stylesheet" type="text/css" href="./css/test-css.css">

        </head>
        <body class="not-main special-background-{{ what_class|lower }}">
    
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
<br><br><br><br><br><br><br><br><br><br>
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
        <div><strong>Name: {{ character['name'] }}</strong></div>
        <div>Level: {{ character['level'] }}</div>
        <div>Class: {{ character['class'] }}</div>
        <div class="character-link">
            <a href="https://pathofdiablo.com/p/armory/?name={{ character['name'] }}" target="_blank">
                {{ character['name'] }}'s Armory
            </a>
        </div>
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
            <br><br>
                    <!-- Embed the Plotly pie chart -->
            <div>
                <img src="charts/{{ what_class }}-clusters_distribution_pie.png" alt="{{ what_class }} Skills Distribution">
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

        def analyze_mercenaries(cluster_files):
            # Dictionary to store mercenary counts and equipment
            mercenary_counts = Counter()
            mercenary_equipment = defaultdict(lambda: defaultdict(Counter))

            # Process each JSON file in the folder
            for filename in os.listdir(data_folder):
                if filename.endswith(".json"):
                    filepath = os.path.join(data_folder, filename)
                    try:
                        # Check if the file is empty
                        if os.path.getsize(filepath) == 0:
                            continue

                        # Parse the JSON
                        with open(filepath, "r") as file:
                            char_data = json.load(file)
                            mercenary = char_data.get("MercenaryType")
                            if mercenary:
                                # Count mercenary types
                                readable_mercenary, _ = map_readable_names(mercenary, "")
                                mercenary_counts[readable_mercenary] += 1
                                
                                # Count mercenary equipment titles by worn category
                                for item in char_data.get("MercenaryEquipped", []):
                                    worn_category = item.get("Worn", "Unknown")
                                    readable_mercenary, readable_worn = map_readable_names(mercenary, worn_category)
                                    title = item.get("Title", "Unknown")
                                    mercenary_equipment[readable_mercenary][readable_worn][title] += 1
                    except json.JSONDecodeError:
                        continue
                    except OSError:
                        continue
            return mercenary_counts, mercenary_equipment
    
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
            mercenary_counts, mercenary_equipment = analyze_mercenaries(cluster_files)

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
                f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
                f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
                        f"<img src='{icons_folder}/{skill}.png' alt='{skill}' width='20' height='20'> "
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
                                <div class="skill-bar" style="width: {percent * 6}px; min-width: 300px;">
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
            mercenary_counts, mercenary_equipment = analyze_mercenaries(data_folder)
    

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

        # Render the HTML report
        template = Template(html_template)
        html_content = template.render(clusters=sorted_clusters, what_class=what_class, top_5_most_used_skills=top_5_most_used_skills, bottom_5_least_used_skills=bottom_5_least_used_skills, summary_label=summary_label, merc_count=merc_count, mercenary=mercenary, mercenary_equipment=mercenary_equipment, timeStamp=timeStamp, full_summary_output=full_summary_output, fun_facts_html=fun_facts_html)  # Pass sorted clusters to the template

        # Save the report to a file
        output_file = f"pod-stats/{what_class}.html"
        with open(output_file, "w") as file:
            file.write(html_content)

        print(f"Cluster analysis report saved to {output_file}")
    pass

    # Iterate through the list and generate reports for each class
    for cls in classes:
        generate_report(cls["data_folder"], cls["what_class"], cls["howmany_clusters"], cls["howmany_skills"])



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

