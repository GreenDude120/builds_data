
#!/usr/bin/env python3
"""
Updated update_csv.py for unified CSV format
This script is now a wrapper around the new API integration system
"""

def update_csv_and_web():
    """
    DEPRECATED: This function has been replaced by the new unified API integration.
    
    Please use api_integration.py instead:
    - For full updates: python3 api_integration.py
    - For testing: python3 api_integration.py test  
    - For monitoring: python3 api_integration.py monitor
    - For custom snapshots: python3 api_integration.py YourSnapshotName
    """
    
    print("⚠️  WARNING: This script has been updated for the new unified CSV format!")
    print("")
    print("🔄 The new system automatically handles:")
    print("   ✅ SC and HC character data")
    print("   ✅ Live server statistics")
    print("   ✅ Individual game server metrics")
    print("   ✅ Unified CSV with proper league separation")
    print("")
    print("📚 How to use the new system:")
    print("   🚀 Full update: python3 api_integration.py")
    print("   🧪 Test APIs: python3 api_integration.py test")
    print("   📊 Monitor: python3 api_integration.py monitor")
    print("   📅 Custom: python3 api_integration.py November_2025")
    print("")
    print("📁 Your data is now in 'unified-usage-over-time.csv'")
    print("🔧 Update your analysis scripts to use the new format!")
    
    # Offer to run the new system
    try:
        user_input = input("\n❓ Would you like to run a full update now? (y/n): ").lower()
        if user_input in ['y', 'yes']:
            print("\n🚀 Running new API integration...")
            import subprocess
            result = subprocess.run(['python3', 'api_integration.py'], 
                                 capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
        else:
            print("👍 No problem! Run 'python3 api_integration.py' when ready.")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    update_csv_and_web()

            # Count Mercenary items
            for item in char.get("MercenaryEquipped", []):
                quality_code = item.get("QualityCode")
                name = item.get("Title")
                if not name:
                    continue

                if quality_code == "q_runeword":
                    key = (name, "", "Mercenary Runeword")
                elif quality_code == "q_set":
                    key = (name, "", "Mercenary Set")
                elif quality_code == "q_unique":
                    key = (name, "", "Mercenary Unique")
                else:
                    continue

                is_synth = "Synthesized" in item.get("Tag", "")
                usage_counter[key][1 if is_synth else 0] += 1


        # Ensure the snapshot label is in the header
        if snapshot_label not in fieldnames:
            fieldnames.append(snapshot_label)
            for row in rows:
                row[snapshot_label] = "0"

        # Update rows
        for (name, cls, typ), (normal, synth) in usage_counter.items():
            row_key = (name, cls, typ)
            if row_key in row_lookup:
                if synth:
                    value = f"{normal}(+{synth})"
                else:
                    value = str(normal)
                row_lookup[row_key][snapshot_label] = value
            else:
                new_row = {k: "0" for k in fieldnames}
                new_row["Name"] = name
                new_row["Class"] = cls
                new_row["Type"] = typ
                if synth:
                    value = f"{normal}(+{synth})"
                else:
                    value = str(normal)
                new_row[snapshot_label] = value
                rows.append(new_row)
                row_lookup[row_key] = new_row  # ✅ This is what you're missing

        # Save the updated CSV
        with open(csv_path, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


    # Load JSON data before passing it to the function
    with open("sc_ladder.json") as f:
        sample_characters = json.load(f)

    update_csv_from_api_response(sample_characters, csv_file_path, sample_snapshot_label)




    # Load CSV data into structured sections
    def read_csv(csv_path):
        sections = {
            "Skills": {},
            "Uniques": [],
            "Sets": [],
            "Runewords": [],
            "Mercenary Uniques": [],  # ✅ new
            "Mercenary Sets": [],     # ✅ new
            "Mercenary Runewords": [] # ✅ new
        }

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames  # Capture all snapshot headers

            for row in reader:
                typ = row["Type"]
                cls = row.get("Class", "").strip()
                name = row["Name"]
                snapshots = {header: row[header] for header in headers if header not in ["Type", "Class", "Name"]}

                if typ == "Skill":
                    if cls not in sections["Skills"]:
                        sections["Skills"][cls] = []
                    sections["Skills"][cls].append((name, snapshots))
                elif typ == "Unique":
                    sections["Uniques"].append((name, snapshots))
                elif typ == "Set":
                    sections["Sets"].append((name, snapshots))
                elif typ == "Runeword":
                    sections["Runewords"].append((name, snapshots))
                elif typ in ["Mercenary Unique", "Mercenary Set", "Mercenary Runeword"]:
                    sections[typ + "s"].append((name, snapshots))  
        return headers, sections

    # Generate formatted HTML output
    def create_html(headers, sections, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("""
            <html>
            <head>
            <title>Usage Over Time</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                #tooltipChart {
                position: absolute;
                display: none;
                border: 1px solid #aaa;
                background-color: #fff;
                z-index: 9999;
                padding: 6px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
                }
            </style>
            </head>
            <body>
            <canvas id="tooltipChart" width="300" height="150"></canvas>
            <h1>Skill and item usage over time</h1>
            <p><i>Click columns to sort</i></p>
            <p><i>Elipses indicate additional synthesized items</i></p>
            """)

            # Skills grouped by class
            f.write("<h2>Skills</h2>\n")
            for cls, skills in sections["Skills"].items():
                f.write(f"""<h3>{cls}</h3>
                <table border='1'>
                <tr><th onclick='sortTable(this, "str")'>Skill</th>""" +
                        "".join(f"<th onclick='sortTable(this, \"num\")'>{header}</th>" for header in headers if header not in ['Type', 'Class', 'Name']) +
                        "</tr>\n")

                for name, snapshots in skills:
                    usage_data = json.dumps(snapshots)
                    f.write(f"<tr><td class='usage-label' data-usage='{usage_data}'>{name}</td>" +
                            "".join(f"<td>{snapshots[header]}</td>" for header in snapshots) + "</tr>\n")
                f.write("</table>\n")

            # Items (Uniques, Sets, Runewords)
            for category in [
                "Uniques", "Sets", "Runewords",
                "Mercenary Uniques", "Mercenary Sets", "Mercenary Runewords"  # ✅ added
            ]:
                f.write(f"""<h2>{category}</h2>
                <table border='1'>
                <tr><th onclick='sortTable(this, "str")'>Name</th>""" +
                        "".join(f"<th onclick='sortTable(this, \"num\")'>{header}</th>" for header in headers if header not in ["Type", "Class", "Name"]) +
                        "</tr>\n")
                for name, snapshots in sections[category]:
                    usage_data = json.dumps({k: v for k, v in snapshots.items()})
                    f.write(f"<tr><td class='usage-label' data-usage='{usage_data}'>{name}</td>" +
                            "".join(f"<td>{snapshots[header]}</td>" for header in snapshots) + "</tr>\n")
                f.write("</table>\n")

            f.write("""
            <script>
            document.addEventListener('DOMContentLoaded', () => {
            const canvas = document.getElementById('tooltipChart');
            const ctx = canvas.getContext('2d');
            let chart;

            document.querySelectorAll('.usage-label').forEach(label => {
                label.addEventListener('mouseenter', e => {
                const data = JSON.parse(label.dataset.usage);
                const labels = Object.keys(data);
                const values = Object.values(data).map(v => parseInt(v));

                if (chart) chart.destroy();
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                    labels: labels,
                    datasets: [{
                        label: label.textContent + ' usage',
                        data: values,
                        borderColor: '#3b82f6',
                        fill: false
                    }]
                    },
                    options: {
                    responsive: false,
                    animation: false,
                    plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: label.textContent + ' Usage Over Time',
                        font: { size: 14, weight: 'bold' },
                        padding: { bottom: 10 }
                    }
                    },
                    scales: {
                        y: { beginAtZero: true },
                        x: { ticks: { maxRotation: 90, minRotation: 45 } }
                    }
                    }
                });

                canvas.style.left = (e.pageX + 10) + 'px';
                canvas.style.top = (e.pageY - 80) + 'px';
                canvas.style.display = 'block';
                });

                label.addEventListener('mouseleave', () => {
                canvas.style.display = 'none';
                });
            });
            });
            </script>
            <script>
            function sortTable(header, type) {
            const th = header;
            const table = th.closest('table');
            const tbody = table.querySelector('tbody') || table;
            const rows = Array.from(tbody.querySelectorAll('tr')).slice(1);
            const colIndex = Array.from(th.parentNode.children).indexOf(th);

            let asc = th.dataset.sortAsc !== "true"; // Toggle direction
            th.dataset.sortAsc = asc;

            rows.sort((a, b) => {
                let valA = a.cells[colIndex].textContent.trim();
                let valB = b.cells[colIndex].textContent.trim();
                if (type === 'num') {
                    valA = parseFloat(valA.replace(/\(\+\d+\)/, "")) || 0;
                    valB = parseFloat(valB.replace(/\(\+\d+\)/, "")) || 0;
                }
                return asc
                ? valA > valB ? 1 : valA < valB ? -1 : 0
                : valA < valB ? 1 : valA > valB ? -1 : 0;
            });

            rows.forEach(row => tbody.appendChild(row));
            }
            </script>
                    
            """)

    # File paths
    csv_file = "sc-usage-over-time.csv"  # Update this with the actual CSV path
    html_file = "sc-usage-over-time.html"

    # Process data and create HTML
    headers, sections = read_csv(csv_file)
    create_html(headers, sections, html_file)

    print("HTML file generated successfully!")

#update_csv_and_web()


def update_hc_csv_and_web():
    import csv
    from collections import defaultdict
    from datetime import date
    import json
    # Sample character data would be passed into this function
    sample_snapshot_label = "August"  # or e.g., f"Day {days_since_ladder_start}"
# Archival data
#    sample_characters = "/home/derek/Desktop/prod-pod-data/builds_data/Season/13/May/sc_ladder.json"
    sample_characters = "hc_ladder.json"  
    csv_file_path = "hc-usage-over-time.csv"
    def update_csv_from_api_response(characters, csv_path, snapshot_label):
        # Load existing CSV into memory
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames

        # Create a quick lookup from name/class/type to row
        row_lookup = {(row['Name'], row.get('Class', ''), row['Type']): row for row in rows}

        # Tally usage counters
        usage_counter = defaultdict(lambda: [0, 0])  # [normal, synth]

        for char in characters:
            cls = char.get("Class")
            for tab in char.get("SkillTabs", []):
                for skill in tab.get("Skills", []):
                    key = (skill["Name"], cls, "Skill")
                    usage_counter[key][0] += skill["Level"]
            
            for item in char.get("Equipped", []):
                quality_code = item.get("QualityCode")
                name = item.get("Title")
                if not name:
                    continue

                if quality_code == "q_runeword":
                    key = (name, "", "Runeword")
                elif quality_code == "q_set":
                    key = (name, "", "Set")
                elif quality_code == "q_unique":
                    key = (name, "", "Unique")
                else:
                    continue

                is_synth = "Synthesized" in item.get("Tag", "")
                usage_counter[key][1 if is_synth else 0] += 1

            # Count Mercenary items
            for item in char.get("MercenaryEquipped", []):
                quality_code = item.get("QualityCode")
                name = item.get("Title")
                if not name:
                    continue

                if quality_code == "q_runeword":
                    key = (name, "", "Mercenary Runeword")
                elif quality_code == "q_set":
                    key = (name, "", "Mercenary Set")
                elif quality_code == "q_unique":
                    key = (name, "", "Mercenary Unique")
                else:
                    continue

                is_synth = "Synthesized" in item.get("Tag", "")
                usage_counter[key][1 if is_synth else 0] += 1

        # Ensure the snapshot label is in the header
        if snapshot_label not in fieldnames:
            fieldnames.append(snapshot_label)
            for row in rows:
                row[snapshot_label] = "0"

        # Update rows
        for (name, cls, typ), (normal, synth) in usage_counter.items():
            row_key = (name, cls, typ)
            if row_key in row_lookup:
                if synth:
                    value = f"{normal}(+{synth})"
                else:
                    value = str(normal)
                row_lookup[row_key][snapshot_label] = value
            else:
                new_row = {k: "0" for k in fieldnames}
                new_row["Name"] = name
                new_row["Class"] = cls
                new_row["Type"] = typ
                if synth:
                    value = f"{normal}(+{synth})"
                else:
                    value = str(normal)
                new_row[snapshot_label] = value
                rows.append(new_row)
                row_lookup[row_key] = new_row  

        # Save the updated CSV
        with open(csv_path, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


    # Load JSON data before passing it to the function
    with open("hc_ladder.json") as f:
        sample_characters = json.load(f)

    update_csv_from_api_response(sample_characters, csv_file_path, sample_snapshot_label)




    # Load CSV data into structured sections
    def read_csv(csv_path):
        sections = {
            "Skills": {},
            "Uniques": [],
            "Sets": [],
            "Runewords": [],
            "Mercenary Uniques": [],  # ✅ new
            "Mercenary Sets": [],     # ✅ new
            "Mercenary Runewords": [] # ✅ new            
        }

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames  # Capture all snapshot headers

            for row in reader:
                typ = row["Type"]
                cls = row.get("Class", "").strip()
                name = row["Name"]
                snapshots = {header: row[header] for header in headers if header not in ["Type", "Class", "Name"]}

                if typ == "Skill":
                    if cls not in sections["Skills"]:
                        sections["Skills"][cls] = []
                    sections["Skills"][cls].append((name, snapshots))
                elif typ == "Unique":
                    sections["Uniques"].append((name, snapshots))
                elif typ == "Set":
                    sections["Sets"].append((name, snapshots))
                elif typ == "Runeword":
                    sections["Runewords"].append((name, snapshots))
                elif typ in ["Mercenary Unique", "Mercenary Set", "Mercenary Runeword"]:
                    sections[typ + "s"].append((name, snapshots))     

        return headers, sections

    # Generate formatted HTML output
    def create_html(headers, sections, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("""
            <html>
            <head>
            <title>Usage Over Time, Hardcore</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                #tooltipChart {
                position: absolute;
                display: none;
                border: 1px solid #aaa;
                background-color: #fff;
                z-index: 9999;
                padding: 6px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
                }
            </style>
            </head>
            <body>
            <canvas id="tooltipChart" width="300" height="150"></canvas>
            <h1>Hardcore skill and item usage over time</h1>
            <p><i>Click columns to sort</i></p>
            <p><i>Elipses indicate additional synthesized items</i></p>
            """)

            # Skills grouped by class
            f.write("<h2>Skills</h2>\n")
            for cls, skills in sections["Skills"].items():
                f.write(f"""<h3>{cls}</h3>
                <table border='1'>
                <tr><th onclick='sortTable(this, "str")'>Skill</th>""" +
                        "".join(f"<th onclick='sortTable(this, \"num\")'>{header}</th>" for header in headers if header not in ['Type', 'Class', 'Name']) +
                        "</tr>\n")

                for name, snapshots in skills:
                    usage_data = json.dumps(snapshots)
                    f.write(f"<tr><td class='usage-label' data-usage='{usage_data}'>{name}</td>" +
                            "".join(f"<td>{snapshots[header]}</td>" for header in snapshots) + "</tr>\n")
                f.write("</table>\n")

            # Items (Uniques, Sets, Runewords)
            for category in [
                "Uniques", "Sets", "Runewords",
                "Mercenary Uniques", "Mercenary Sets", "Mercenary Runewords"  # ✅ added
            ]:
                f.write(f"""<h2>{category}</h2>
                <table border='1'>
                <tr><th onclick='sortTable(this, "str")'>Name</th>""" +
                        "".join(f"<th onclick='sortTable(this, \"num\")'>{header}</th>" for header in headers if header not in ["Type", "Class", "Name"]) +
                        "</tr>\n")
                for name, snapshots in sections[category]:
                    usage_data = json.dumps({k: v for k, v in snapshots.items()})
                    f.write(f"<tr><td class='usage-label' data-usage='{usage_data}'>{name}</td>" +
                            "".join(f"<td>{snapshots[header]}</td>" for header in snapshots) + "</tr>\n")
                f.write("</table>\n")

            f.write("""
            <script>
            document.addEventListener('DOMContentLoaded', () => {
            const canvas = document.getElementById('tooltipChart');
            const ctx = canvas.getContext('2d');
            let chart;

            document.querySelectorAll('.usage-label').forEach(label => {
                label.addEventListener('mouseenter', e => {
                const data = JSON.parse(label.dataset.usage);
                const labels = Object.keys(data);
                const values = Object.values(data).map(v => parseInt(v));

                if (chart) chart.destroy();
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                    labels: labels,
                    datasets: [{
                        label: label.textContent + ' usage',
                        data: values,
                        borderColor: '#3b82f6',
                        fill: false
                    }]
                    },
                    options: {
                    responsive: false,
                    animation: false,
                    plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: label.textContent + ' Usage Over Time',
                        font: { size: 14, weight: 'bold' },
                        padding: { bottom: 10 }
                    }
                    },
                    scales: {
                        y: { beginAtZero: true },
                        x: { ticks: { maxRotation: 90, minRotation: 45 } }
                    }
                    }
                });

                canvas.style.left = (e.pageX + 10) + 'px';
                canvas.style.top = (e.pageY - 80) + 'px';
                canvas.style.display = 'block';
                });

                label.addEventListener('mouseleave', () => {
                canvas.style.display = 'none';
                });
            });
            });
            </script>
            <script>
            function sortTable(header, type) {
            const th = header;
            const table = th.closest('table');
            const tbody = table.querySelector('tbody') || table;
            const rows = Array.from(tbody.querySelectorAll('tr')).slice(1);
            const colIndex = Array.from(th.parentNode.children).indexOf(th);

            let asc = th.dataset.sortAsc !== "true"; // Toggle direction
            th.dataset.sortAsc = asc;

            rows.sort((a, b) => {
                let valA = a.cells[colIndex].textContent.trim();
                let valB = b.cells[colIndex].textContent.trim();
                if (type === 'num') {
                    valA = parseFloat(valA.replace(/\(\+\d+\)/, "")) || 0;
                    valB = parseFloat(valB.replace(/\(\+\d+\)/, "")) || 0;
                }
                return asc
                ? valA > valB ? 1 : valA < valB ? -1 : 0
                : valA < valB ? 1 : valA > valB ? -1 : 0;
            });

            rows.forEach(row => tbody.appendChild(row));
            }
            </script>
            """)

    # File paths
    csv_file = "hc-usage-over-time.csv"  # Update this with the actual CSV path
    html_file = "hc-usage-over-time.html"

    # Process data and create HTML
    headers, sections = read_csv(csv_file)
    create_html(headers, sections, html_file)

    print("HTML file generated successfully!")

#update_hc_csv_and_web()
