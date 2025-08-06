import requests
import json
import os
import time
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime
import pprint
pp = pprint.PrettyPrinter(indent=4)
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

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
    plt.savefig("charts/1kclass_distribution.png", dpi=300, bbox_inches='tight', transparent=True)
    plt.close()  # Avoid memory issues
    print("✅ Pie chart saved as 1kclass_distribution.png")

def fetch_ladder_characters(base_ladder_url, start_page=1, end_page=5):
    all_characters = []
    for page in range(start_page, end_page + 1):
        url = f"{base_ladder_url}{page}"
        print(f"Fetching {url}")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            all_characters.extend(data.get("ladder", []))
        else:
            print(f"⚠️ Failed to fetch page {page}: {response.status_code}")
    return all_characters

def fetch_1kladder_characters(base_ladder_url, pages):
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

def fetch_char_summaries(characters):
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"
    final_data = []
    for character in characters:
        char_name = character.get("charName", "unknown")
        char_id = character.get("id", None)

        if char_name == "unknown":
            char_name = f"unknown_{char_id or int(time.time() * 1000)}"

        response = requests.get(char_url.format(char_name=char_name))
        if response.status_code == 200:
            final_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character summary: {char_name}")
    return final_data


def generate_class_distribution_chart(characters, output_path):
    class_counts = Counter(char.get("class", "Unknown") for char in characters)
    labels = list(class_counts.keys())
    sizes = list(class_counts.values())

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title("Class Distribution")
    plt.axis("equal")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight", transparent=True)
    plt.close()


def fetch_all_char_data(mode):
    print(f"=== Fetching {mode.upper()} Ladder ===")
    is_hc = mode == "hc"

    base_url = f"https://beta.pathofdiablo.com/api/ladder/13/{'1' if is_hc else '0'}/"
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"

    # Step 1: Fetch only the top 1,000 characters (pages 0–5)
    top_1k_characters = fetch_ladder_characters(f"{base_url}0/", 5)
    top_1k_dict = {char["charName"]: char for char in top_1k_characters}
    top_1k_unique = list(top_1k_dict.values())

    # Step 2: Generate pie chart based ONLY on top 1,000
    class_counts = count_classes(top_1k_unique)
    generate_pie_chart(class_counts)

    # Step 3: Add class-specific characters to build the full data set
    all_characters = top_1k_unique.copy()

    for _, suffix in classes.items():
        class_url = base_url + suffix
        all_characters.extend(fetch_ladder_characters(class_url, start_page=1, end_page=1))

    # Deduplicate everything (for json saving and summary fetching)
    unique_characters = {char["charName"]: char for char in all_characters}.values()
    # Top 200 per class
    classes = {
        "Amazon": "1/",
        "Assassin": "7/",
        "Barbarian": "5/",
        "Druid": "6/",
        "Necromancer": "3/",
        "Paladin": "4/",
        "Sorceress": "2/"
    }

    for _, suffix in classes.items():
        class_url = base_url + suffix
        all_characters.extend(fetch_ladder_characters(class_url, start_page=1, end_page=1))

    # Deduplicate
    unique_characters = {char["charName"]: char for char in all_characters}.values()

    # Save raw ladder
#    raw_filename = f"raw_ladder_{mode}.json"
    raw_filename = f"{mode}_raw_ladder.json"
    with open(raw_filename, "w") as f:
        json.dump(list(unique_characters), f, indent=2)

    # Fetch full summaries
    full_summaries = fetch_char_summaries(unique_characters)

    # Save full summaries
#    full_filename = f"ladder_{mode}.json"
    full_filename = f"{mode}_ladder.json"
    with open(full_filename, "w") as f:
        json.dump(full_summaries, f, indent=2)

    # Save class chart
    chart_path = f"charts/class_distribution_{mode}.png"
    generate_class_distribution_chart(full_summaries, chart_path)

    print(f"✅ {mode.upper()} complete: {len(full_summaries)} characters")
    print(f"📄 JSON saved to {full_filename}")
    print(f"📈 Chart saved to {chart_path}")


def main():
    fetch_all_char_data("sc")
    fetch_all_char_data("hc")


if __name__ == "__main__":
    main()
