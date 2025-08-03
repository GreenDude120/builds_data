import requests
import json
import os
import time
from collections import Counter
import matplotlib.pyplot as plt


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

    # Top 1000
    all_characters = fetch_ladder_characters(base_url, start_page=1, end_page=5)

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
