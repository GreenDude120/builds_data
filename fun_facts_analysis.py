import pandas as pd
import numpy as np

def load_and_process_data():
    """Load both CSV files and combine the data for analysis"""
    
    # Load the softcore and hardcore usage data from CSV files
    sc_df = pd.read_csv('sc-usage-over-time.csv')
    hc_df = pd.read_csv('hc-usage-over-time.csv')
    
    # Convert all time period columns to numeric, replacing any invalid values with 0
    # This ensures we can do mathematical operations on the data
    time_columns = ['March', 'April', 'May', 'June', 'July', 'August', 'S13 September', 'S13 October','End of Season']
    for col in time_columns:
        sc_df[col] = pd.to_numeric(sc_df[col], errors='coerce').fillna(0)
        hc_df[col] = pd.to_numeric(hc_df[col], errors='coerce').fillna(0)
    
    # Add a column to identify which league (Softcore/Hardcore) each row belongs to
    sc_df['League'] = 'Softcore'
    hc_df['League'] = 'Hardcore'
    
    # Combine both datasets into one big dataframe for easier analysis
    combined_df = pd.concat([sc_df, hc_df], ignore_index=True)
    
    return sc_df, hc_df, combined_df

def calculate_totals(df):
    """Use only End of Season data for analysis (not cumulative across months)"""
    # We use the final snapshot rather than summing months to avoid double-counting
    df['Total_Usage'] = df['End of Season']
    return df

def analyze_skills(combined_df):
    """Analyze skill usage patterns across both leagues"""
    # Filter to only skill data (exclude items) and prepare for analysis
    skills_df = combined_df[combined_df['Type'] == 'Skill'].copy()
    skills_df = calculate_totals(skills_df)
    
    print("🎯 SKILL ANALYSIS (End of Season 13)")
    print("=" * 50)
    
    # Find the most popular skills by combining SC + HC usage
    most_popular = skills_df.groupby(['Name', 'Class'])['Total_Usage'].sum().sort_values(ascending=False).head(10)
    print("\n🔥 TOP 10 MOST POPULAR SKILLS (Season End - Combined SC + HC):")
    for i, ((skill, char_class), total) in enumerate(most_popular.items(), 1):
        print(f"{i:2d}. {skill} ({char_class}): {total:,} points")
    
    # Find the least popular skills (but still used)
    least_popular = skills_df.groupby(['Name', 'Class'])['Total_Usage'].sum().sort_values().head(10)
    print("\n❄️ TOP 10 LEAST POPULAR SKILLS (Season End - Combined SC + HC):")
    for i, ((skill, char_class), total) in enumerate(least_popular.items(), 1):
        print(f"{i:2d}. {skill} ({char_class}): {total:,} points")
    
    # Compare Softcore vs Hardcore preferences for each skill
    # This shows which skills are preferred by which league
    skill_comparison = skills_df.groupby(['Name', 'Class', 'League'])['Total_Usage'].sum().unstack('League', fill_value=0)
    skill_comparison['SC_Ratio'] = skill_comparison['Softcore'] / (skill_comparison['Softcore'] + skill_comparison['Hardcore'])
    skill_comparison['HC_Ratio'] = skill_comparison['Hardcore'] / (skill_comparison['Softcore'] + skill_comparison['Hardcore'])
    skill_comparison['Total'] = skill_comparison['Softcore'] + skill_comparison['Hardcore']
    
    # Only look at skills with meaningful usage to avoid statistical noise
    meaningful_skills = skill_comparison[skill_comparison['Total'] >= 100]
    
    # Show skills that Softcore players heavily prefer
    sc_favorites = meaningful_skills.sort_values('SC_Ratio', ascending=False).head(10)
    print("\n💙 SKILLS PREFERRED IN SOFTCORE:")
    for (skill, char_class), row in sc_favorites.iterrows():
        print(f"   {skill} ({char_class}): {row['SC_Ratio']:.1%} SC vs {row['HC_Ratio']:.1%} HC")
    
    # Show skills that Hardcore players heavily prefer
    hc_favorites = meaningful_skills.sort_values('HC_Ratio', ascending=False).head(10)
    print("\n❤️ SKILLS PREFERRED IN HARDCORE:")
    for (skill, char_class), row in hc_favorites.iterrows():
        print(f"   {skill} ({char_class}): {row['HC_Ratio']:.1%} HC vs {row['SC_Ratio']:.1%} SC")
    
    return skills_df

def analyze_items(combined_df):
    """Analyze item usage patterns across both leagues"""
    # Filter to only item data (exclude skills) and prepare for analysis
    items_df = combined_df[combined_df['Type'] != 'Skill'].copy()
    items_df = calculate_totals(items_df)
    
    print("\n\n⚔️ ITEM ANALYSIS (End of Season)")
    print("=" * 50)
    
    # Find the most popular items by combining SC + HC usage
    most_popular_items = items_df.groupby(['Name', 'Type'])['Total_Usage'].sum().sort_values(ascending=False).head(15)
    print("\n🏆 TOP 15 MOST POPULAR ITEMS (Season End - Combined SC + HC):")
    for i, ((item, item_type), total) in enumerate(most_popular_items.items(), 1):
        print(f"{i:2d}. {item} ({item_type}): {total:,} uses")
    
    # Find rarely used items (but not completely unused ones)
    least_popular_items = items_df[items_df['Total_Usage'] > 0].groupby(['Name', 'Type'])['Total_Usage'].sum().sort_values().head(10)
    print("\n🗂️ TOP 10 LEAST POPULAR ITEMS (Season End - But still used):")
    for i, ((item, item_type), total) in enumerate(least_popular_items.items(), 1):
        print(f"{i:2d}. {item} ({item_type}): {total:,} uses")
    
    # Show total usage by item category (Runewords, Uniques, Sets, etc.)
    print("\n📊 ITEMS BY TYPE:")
    type_totals = items_df.groupby('Type')['Total_Usage'].sum().sort_values(ascending=False)
    for item_type, total in type_totals.items():
        print(f"   {item_type}: {total:,} total uses")
    
    # Compare Softcore vs Hardcore preferences for each item
    # This reveals interesting differences in risk tolerance and economy
    item_comparison = items_df.groupby(['Name', 'Type', 'League'])['Total_Usage'].sum().unstack('League', fill_value=0)
    item_comparison['SC_Ratio'] = item_comparison['Softcore'] / (item_comparison['Softcore'] + item_comparison['Hardcore'])
    item_comparison['HC_Ratio'] = item_comparison['Hardcore'] / (item_comparison['Softcore'] + item_comparison['Hardcore'])
    item_comparison['Total'] = item_comparison['Softcore'] + item_comparison['Hardcore']
    
    # Only look at items with meaningful usage to avoid statistical noise
    meaningful_items = item_comparison[item_comparison['Total'] >= 20]
    
    # Show items that Softcore players heavily prefer (often expensive/risky items)
    sc_item_favorites = meaningful_items.sort_values('SC_Ratio', ascending=False).head(10)
    print("\n💙 ITEMS PREFERRED IN SOFTCORE:")
    for (item, item_type), row in sc_item_favorites.iterrows():
        print(f"   {item} ({item_type}): {row['SC_Ratio']:.1%} SC vs {row['HC_Ratio']:.1%} HC")
    
    # Show items that Hardcore players heavily prefer (often cheap/safe items)
    hc_item_favorites = meaningful_items.sort_values('HC_Ratio', ascending=False).head(10)
    print("\n❤️ ITEMS PREFERRED IN HARDCORE:")
    for (item, item_type), row in hc_item_favorites.iterrows():
        print(f"   {item} ({item_type}): {row['HC_Ratio']:.1%} HC vs {row['SC_Ratio']:.1%} SC")
    
    return items_df

def analyze_class_specialization(combined_df):
    """Discover which classes are most specialized vs generalized in their skill usage"""
    print("\n\n🎭 CLASS SPECIALIZATION ANALYSIS")
    print("=" * 50)
    
    skills_df = combined_df[combined_df['Type'] == 'Skill'].copy()
    skills_df = calculate_totals(skills_df)
    
    # Calculate specialization by looking at skill distribution within each class
    class_stats = {}
    for char_class in skills_df['Class'].unique():
        class_skills = skills_df[skills_df['Class'] == char_class]
        total_points = class_skills['Total_Usage'].sum()
        skill_counts = class_skills.groupby('Name')['Total_Usage'].sum().sort_values(ascending=False)
        
        # Calculate what % of total points go to the top skill
        top_skill_ratio = skill_counts.iloc[0] / total_points if len(skill_counts) > 0 else 0
        
        # Count how many skills have meaningful usage (>1% of class total)
        meaningful_skills = len(skill_counts[skill_counts >= (total_points * 0.01)])
        
        class_stats[char_class] = {
            'total_points': total_points,
            'top_skill': skill_counts.index[0] if len(skill_counts) > 0 else 'None',
            'top_skill_points': skill_counts.iloc[0] if len(skill_counts) > 0 else 0,
            'top_skill_ratio': top_skill_ratio,
            'meaningful_skills': meaningful_skills
        }
    
    print("\n🎯 MOST SPECIALIZED CLASSES (High % in top skill):")
    specialized = sorted(class_stats.items(), key=lambda x: x[1]['top_skill_ratio'], reverse=True)
    for char_class, stats in specialized:
        print(f"   {char_class}: {stats['top_skill_ratio']:.1%} of points in {stats['top_skill']} ({stats['top_skill_points']:,} points)")
    
    print("\n🌈 MOST DIVERSE CLASSES (More skills with meaningful usage):")
    diverse = sorted(class_stats.items(), key=lambda x: x[1]['meaningful_skills'], reverse=True)
    for char_class, stats in diverse:
        print(f"   {char_class}: {stats['meaningful_skills']} skills with 1%+ usage")

def analyze_mercenary_economy(combined_df):
    """Analyze the mercenary item meta - what are mercs wearing?"""
    print("\n\n🛡️ MERCENARY EQUIPMENT ANALYSIS")
    print("=" * 50)
    
    merc_df = combined_df[combined_df['Type'].str.contains('Mercenary', na=False)].copy()
    merc_df = calculate_totals(merc_df)
    
    if len(merc_df) == 0:
        print("No mercenary data found!")
        return
    
    # Most popular mercenary items
    top_merc_items = merc_df.groupby(['Name', 'Type'])['Total_Usage'].sum().sort_values(ascending=False).head(10)
    print("\n⚔️ TOP 10 MERCENARY ITEMS:")
    for i, ((item, item_type), total) in enumerate(top_merc_items.items(), 1):
        print(f"{i:2d}. {item} ({item_type}): {total:,} uses")
    
    # Mercenary items by type
    print("\n📊 MERCENARY GEAR BY TYPE:")
    merc_type_totals = merc_df.groupby('Type')['Total_Usage'].sum().sort_values(ascending=False)
    for item_type, total in merc_type_totals.items():
        print(f"   {item_type}: {total:,} total uses")
    
    # Compare mercenary vs player item usage
    player_items = combined_df[~combined_df['Type'].str.contains('Mercenary|Skill', na=False)]
    player_total = calculate_totals(player_items)['Total_Usage'].sum()
    merc_total = merc_df['Total_Usage'].sum()
    
    print(f"\n🎭 PLAYER vs MERCENARY ECONOMY:")
    print(f"   Player Items: {player_total:,} uses")
    print(f"   Mercenary Items: {merc_total:,} uses")
    if player_total > 0:
        ratio = player_total / merc_total if merc_total > 0 else float('inf')
        print(f"   Players use {ratio:.1f}x more items than mercenaries")

def analyze_forgotten_skills(combined_df):
    """Find the most forgotten and underused skills"""
    print("\n\n👻 FORGOTTEN SKILLS ANALYSIS")
    print("=" * 50)
    
    skills_df = combined_df[combined_df['Type'] == 'Skill'].copy()
    skills_df = calculate_totals(skills_df)
    
    # Skills with ZERO usage
    zero_usage = skills_df[skills_df['Total_Usage'] == 0].groupby(['Name', 'Class']).size()
    if len(zero_usage) > 0:
        print(f"\n💀 COMPLETELY UNUSED SKILLS ({len(zero_usage)} total):")
        for (skill, char_class) in zero_usage.index:
            print(f"   {skill} ({char_class}): 0 points allocated!")
    
    # Skills with very low usage (1-10 points total)
    ultra_rare = skills_df[(skills_df['Total_Usage'] > 0) & (skills_df['Total_Usage'] <= 10)]
    ultra_rare_grouped = ultra_rare.groupby(['Name', 'Class'])['Total_Usage'].sum().sort_values()
    
    print(f"\n🦄 ULTRA-RARE SKILLS (1-10 total points, {len(ultra_rare_grouped)} skills):")
    for (skill, char_class), total in ultra_rare_grouped.head(10).items():
        print(f"   {skill} ({char_class}): {total} points")
    
    # Calculate what % of all skills are "forgotten" (under 50 points)
    all_skills = skills_df.groupby(['Name', 'Class'])['Total_Usage'].sum()
    forgotten_threshold = 50
    forgotten_skills = all_skills[all_skills < forgotten_threshold]
    forgotten_percentage = len(forgotten_skills) / len(all_skills) * 100
    
    print(f"\n📊 SKILL USAGE DISTRIBUTION:")
    print(f"   Total skills tracked: {len(all_skills)}")
    print(f"   Skills with <{forgotten_threshold} points: {len(forgotten_skills)} ({forgotten_percentage:.1f}%)")
    print(f"   Skills with 0 points: {len(all_skills[all_skills == 0])}")

def analyze_league_risk_tolerance(combined_df):
    """Analyze risk tolerance differences between SC and HC through item choices"""
    print("\n\n⚖️ RISK TOLERANCE ANALYSIS")
    print("=" * 50)
    
    items_df = combined_df[combined_df['Type'] != 'Skill'].copy()
    items_df = calculate_totals(items_df)
    
    # Define "expensive" items (likely high-value/risky to lose)
    expensive_keywords = ['Death\'s', 'Nightwing', 'Infinity', 'Enigma', 'Bramble', 'Phoenix', 'Dragon']
    cheap_keywords = ['Stealth', 'Lore', 'Sigon\'s', 'Hsarus\'', 'Cathan\'s', 'Arctic']
    
    # Calculate usage ratios for expensive vs cheap items
    item_comparison = items_df.groupby(['Name', 'Type', 'League'])['Total_Usage'].sum().unstack('League', fill_value=0)
    item_comparison['Total'] = item_comparison.get('Softcore', 0) + item_comparison.get('Hardcore', 0)
    item_comparison = item_comparison[item_comparison['Total'] >= 10]  # Filter for meaningful usage
    
    expensive_items = item_comparison[item_comparison.index.get_level_values(0).str.contains('|'.join(expensive_keywords), case=False, na=False)]
    cheap_items = item_comparison[item_comparison.index.get_level_values(0).str.contains('|'.join(cheap_keywords), case=False, na=False)]
    
    if len(expensive_items) > 0:
        expensive_sc = expensive_items.get('Softcore', pd.Series()).sum()
        expensive_hc = expensive_items.get('Hardcore', pd.Series()).sum()
        expensive_total = expensive_sc + expensive_hc
        
        print(f"\n💎 EXPENSIVE/RISKY ITEMS:")
        print(f"   Softcore: {expensive_sc:,} uses ({expensive_sc/expensive_total:.1%})")
        print(f"   Hardcore: {expensive_hc:,} uses ({expensive_hc/expensive_total:.1%})")
    
    if len(cheap_items) > 0:
        cheap_sc = cheap_items.get('Softcore', pd.Series()).sum()
        cheap_hc = cheap_items.get('Hardcore', pd.Series()).sum()
        cheap_total = cheap_sc + cheap_hc
        
        print(f"\n🛡️ BUDGET/SAFE ITEMS:")
        print(f"   Softcore: {cheap_sc:,} uses ({cheap_sc/cheap_total:.1%})")
        print(f"   Hardcore: {cheap_hc:,} uses ({cheap_hc/cheap_total:.1%})")
    
    # Find items that are 90%+ exclusive to one league
    item_comparison['SC_Ratio'] = item_comparison.get('Softcore', 0) / item_comparison['Total']
    item_comparison['HC_Ratio'] = item_comparison.get('Hardcore', 0) / item_comparison['Total']
    
    sc_exclusive = item_comparison[item_comparison['SC_Ratio'] >= 0.9]
    hc_exclusive = item_comparison[item_comparison['HC_Ratio'] >= 0.9]
    
    print(f"\n🔒 LEAGUE-EXCLUSIVE ITEMS (90%+ usage in one league):")
    print(f"   Softcore-exclusive: {len(sc_exclusive)} items")
    print(f"   Hardcore-exclusive: {len(hc_exclusive)} items")

def analyze_power_creep_indicators(combined_df):
    """Look for signs of power creep in the meta"""
    print("\n\n⚡ POWER LEVEL ANALYSIS")
    print("=" * 50)
    
    # Analyze runeword vs unique vs set distribution
    items_df = combined_df[combined_df['Type'] != 'Skill'].copy()
    items_df = calculate_totals(items_df)
    
    type_usage = items_df.groupby('Type')['Total_Usage'].sum().sort_values(ascending=False)
    total_items = type_usage.sum()
    
    print("\n🏆 ITEM TIER POPULARITY:")
    for item_type, usage in type_usage.items():
        percentage = usage / total_items * 100
        print(f"   {item_type}: {usage:,} uses ({percentage:.1f}%)")
    
    # Look at the most dominant single items
    top_items = items_df.groupby('Name')['Total_Usage'].sum().sort_values(ascending=False).head(5)
    
    print(f"\n👑 MOST DOMINANT INDIVIDUAL ITEMS:")
    for item, usage in top_items.items():
        percentage = usage / total_items * 100
        print(f"   {item}: {usage:,} uses ({percentage:.1f}% of all item usage)")

    return items_df

def analyze_meta_evolution(sc_df, hc_df, combined_df):
    """Track how the meta evolved throughout the entire season"""
    print("\n\n📅 META EVOLUTION TIMELINE ANALYSIS")
    print("=" * 50)
    
    # Define all time periods in order
    time_periods = ['March', 'April', 'May', 'June', 'July', 'August', 'S13 September', 'S13 October', 'End of Season']
    
    skills_df = combined_df[combined_df['Type'] == 'Skill'].copy()
    
    print("\n🎯 TOP SKILL BY MONTH (Combined SC + HC):")
    for period in time_periods:
        if period in skills_df.columns:
            # Get the most popular skill for this month
            monthly_totals = skills_df.groupby(['Name', 'Class'])[period].sum().sort_values(ascending=False)
            if len(monthly_totals) > 0:
                top_skill = monthly_totals.index[0]
                top_points = monthly_totals.iloc[0]
                print(f"   {period}: {top_skill[0]} ({top_skill[1]}) - {top_points:,} points")
    
    # Track the rise and fall of specific skills over time
    print("\n📈 SKILL POPULARITY TIMELINE (Selected interesting skills):")
    interesting_skills = [
        ('Fire Blast', 'Assassin'),
        ('Hemorrhage', 'Necromancer'), 
        ('Telekinesis', 'Sorceress'),
        ('Cold Mastery', 'Sorceress'),
        ('Fury', 'Druid')
    ]
    
    for skill_name, char_class in interesting_skills:
        skill_data = skills_df[(skills_df['Name'] == skill_name) & (skills_df['Class'] == char_class)]
        if len(skill_data) > 0:
            print(f"\n   {skill_name} ({char_class}):")
            # Get combined SC + HC data for this skill
            combined_skill = skill_data.groupby('League')[time_periods].sum().sum()
            for period in time_periods:
                if period in combined_skill.index:
                    print(f"     {period}: {combined_skill[period]:,}")

def analyze_seasonal_patterns(combined_df):
    """Look for patterns that emerge at different points in the season"""
    print("\n\n🌊 SEASONAL PATTERN ANALYSIS")
    print("=" * 50)
    
    time_periods = ['March', 'April', 'May', 'June', 'July', 'August', 'S13 September', 'S13 October', 'End of Season']
    
    # Calculate total activity by month
    skills_df = combined_df[combined_df['Type'] == 'Skill'].copy()
    items_df = combined_df[combined_df['Type'] != 'Skill'].copy()
    
    print("\n📊 TOTAL ACTIVITY BY MONTH:")
    print("Skills:")
    for period in time_periods:
        if period in skills_df.columns:
            total = skills_df[period].sum()
            print(f"   {period}: {total:,} skill points")
    
    print("\nItems:")
    for period in time_periods:
        if period in items_df.columns:
            total = items_df[period].sum()
            print(f"   {period}: {total:,} item uses")
    
    # Find skills that had dramatic month-over-month changes
    print("\n🎢 MOST VOLATILE SKILLS (Biggest month-to-month swings):")
    
    # Calculate month-over-month volatility
    skill_volatility = {}
    for _, skill_row in skills_df.iterrows():
        volatility_score = 0
        prev_value = None
        skill_key = (skill_row['Name'], skill_row['Class'], skill_row['League'])
        
        for period in time_periods:
            if period in skill_row.index and prev_value is not None:
                current_value = skill_row[period]
                if prev_value > 0:  # Avoid division by zero
                    month_change = abs(current_value - prev_value) / prev_value
                    volatility_score += month_change
            if period in skill_row.index:
                prev_value = skill_row[period]
        
        if volatility_score > 0:
            skill_volatility[skill_key] = volatility_score
    
    # Show most volatile skills
    most_volatile = sorted(skill_volatility.items(), key=lambda x: x[1], reverse=True)[:10]
    for (skill, char_class, league), volatility in most_volatile:
        print(f"   {skill} ({char_class}, {league}): {volatility:.2f} volatility score")

def analyze_league_divergence_timeline(sc_df, hc_df):
    """Track when SC and HC preferences diverged most"""
    print("\n\n⚖️ LEAGUE DIVERGENCE TIMELINE")
    print("=" * 50)
    
    time_periods = ['March', 'April', 'May', 'June', 'July', 'August', 'S13 September', 'S13 October', 'End of Season']
    
    skills_sc = sc_df[sc_df['Type'] == 'Skill'].copy()
    skills_hc = hc_df[hc_df['Type'] == 'Skill'].copy()
    
    print("\n📊 LEAGUE PREFERENCE DIVERGENCE BY MONTH:")
    
    # For each month, calculate how different the top skills are between leagues
    for period in time_periods:
        if period in skills_sc.columns and period in skills_hc.columns:
            # Get top 10 skills for each league this month
            sc_top = skills_sc.groupby(['Name', 'Class'])[period].sum().sort_values(ascending=False).head(10)
            hc_top = skills_hc.groupby(['Name', 'Class'])[period].sum().sort_values(ascending=False).head(10)
            
            # Calculate overlap
            sc_skills = set(sc_top.index)
            hc_skills = set(hc_top.index)
            overlap = len(sc_skills.intersection(hc_skills))
            overlap_percentage = overlap / 10 * 100
            
            print(f"   {period}: {overlap}/10 skills overlap ({overlap_percentage:.0f}%)")

def analyze_meta_stability(combined_df):
    """Analyze how stable or chaotic the meta was"""
    print("\n\n🎯 META STABILITY ANALYSIS")
    print("=" * 50)
    
    time_periods = ['March', 'April', 'May', 'June', 'July', 'August', 'S13 September', 'S13 October', 'End of Season']
    
    skills_df = combined_df[combined_df['Type'] == 'Skill'].copy()
    items_df = combined_df[combined_df['Type'] != 'Skill'].copy()
    
    # Track how the top 10 skills changed each month
    print("\n📈 TOP 10 SKILLS STABILITY:")
    previous_top10 = None
    
    for period in time_periods:
        if period in skills_df.columns:
            current_top10 = set(skills_df.groupby(['Name', 'Class'])[period].sum().sort_values(ascending=False).head(10).index)
            
            if previous_top10 is not None:
                overlap = len(current_top10.intersection(previous_top10))
                new_entries = len(current_top10 - previous_top10)
                print(f"   {period}: {overlap}/10 skills stayed, {new_entries} new entries")
            else:
                print(f"   {period}: Baseline established")
            
            previous_top10 = current_top10
    
    # Find skills that entered/left the top 10 during the season
    march_top10 = set(skills_df.groupby(['Name', 'Class'])['March'].sum().sort_values(ascending=False).head(10).index)
    final_top10 = set(skills_df.groupby(['Name', 'Class'])['End of Season'].sum().sort_values(ascending=False).head(10).index)
    
    newcomers = final_top10 - march_top10
    dropouts = march_top10 - final_top10
    
    print(f"\n🌟 SKILLS THAT ENTERED TOP 10 DURING SEASON:")
    for skill, char_class in newcomers:
        print(f"   {skill} ({char_class})")
    
    print(f"\n📉 SKILLS THAT LEFT TOP 10 DURING SEASON:")
    for skill, char_class in dropouts:
        print(f"   {skill} ({char_class})")

def analyze_comeback_stories(combined_df):
    """Find skills/items that had dramatic comebacks or falls during the season"""
    print("\n\n🏆 COMEBACK & DOWNFALL STORIES")
    print("=" * 50)
    
    skills_df = combined_df[combined_df['Type'] == 'Skill'].copy()
    
    # Find skills that were low in March but high at end
    march_totals = skills_df.groupby(['Name', 'Class'])['March'].sum()
    final_totals = skills_df.groupby(['Name', 'Class'])['End of Season'].sum()
    
    # Calculate comeback ratio (final/march) for skills with meaningful usage
    comeback_ratios = {}
    for skill in march_totals.index:
        if skill in final_totals.index:
            march_val = march_totals[skill]
            final_val = final_totals[skill]
            if march_val > 10 and final_val > 10:  # Only meaningful usage
                ratio = final_val / march_val
                comeback_ratios[skill] = {
                    'ratio': ratio,
                    'march': march_val,
                    'final': final_val,
                    'change': final_val - march_val
                }
    
    # Biggest comebacks (low start, high finish)
    comebacks = sorted(comeback_ratios.items(), key=lambda x: x[1]['ratio'], reverse=True)[:5]
    print("\n🌟 BIGGEST COMEBACK STORIES (March → End of Season):")
    for (skill, char_class), data in comebacks:
        print(f"   {skill} ({char_class}): {data['march']:.0f} → {data['final']:.0f} ({data['ratio']:.1f}x growth)")
    
    # Biggest falls (high start, low finish)
    falls = sorted(comeback_ratios.items(), key=lambda x: x[1]['ratio'])[:5]
    print("\n📉 BIGGEST DOWNFALL STORIES (March → End of Season):")
    for (skill, char_class), data in falls:
        print(f"   {skill} ({char_class}): {data['march']:.0f} → {data['final']:.0f} ({data['ratio']:.1f}x decline)")

def analyze_trends(sc_df, hc_df):
    """Analyze how skills changed in popularity from season start to end"""
    print("\n\n📈 TREND ANALYSIS")
    print("=" * 50)
    
    # Define all time periods we have data for (not all used in this analysis)
    time_columns = ['March', 'April', 'May', 'June', 'July', 'August', 'S13 September', 'S13 October','End of Season']

    # Separate skill data for each league to compare trends
    sc_skills = sc_df[sc_df['Type'] == 'Skill'].copy()
    hc_skills = hc_df[hc_df['Type'] == 'Skill'].copy()
    
    # Calculate the change from season start (March) to season end
    # Positive = skill gained popularity, Negative = skill lost popularity
    sc_skills['Growth'] = sc_skills['End of Season'] - sc_skills['March']
    hc_skills['Growth'] = hc_skills['End of Season'] - hc_skills['March']

    # Show the skills that gained the most popularity during the season
    print("\n📈 BIGGEST SKILL GAINERS (March to End of Season):")
    print("Softcore:")
    top_sc_gainers = sc_skills.nlargest(5, 'Growth')[['Name', 'Class', 'March', 'End of Season', 'Growth']]
    for _, row in top_sc_gainers.iterrows():
        print(f"   {row['Name']} ({row['Class']}): {row['March']} → {row['End of Season']} (+{row['Growth']})")

    print("Hardcore:")
    top_hc_gainers = hc_skills.nlargest(5, 'Growth')[['Name', 'Class', 'March', 'End of Season', 'Growth']]
    for _, row in top_hc_gainers.iterrows():
        print(f"   {row['Name']} ({row['Class']}): {row['March']} → {row['End of Season']} (+{row['Growth']})")

    # Show the skills that lost the most popularity during the season
    print("\n📉 BIGGEST SKILL LOSERS (March to End of Season):")
    print("Softcore:")
    top_sc_losers = sc_skills.nsmallest(5, 'Growth')[['Name', 'Class', 'March', 'End of Season', 'Growth']]
    for _, row in top_sc_losers.iterrows():
        print(f"   {row['Name']} ({row['Class']}): {row['March']} → {row['End of Season']} ({row['Growth']})")

    print("Hardcore:")
    top_hc_losers = hc_skills.nsmallest(5, 'Growth')[['Name', 'Class', 'March', 'End of Season', 'Growth']]
    for _, row in top_hc_losers.iterrows():
        print(f"   {row['Name']} ({row['Class']}): {row['March']} → {row['End of Season']} ({row['Growth']})")

def fun_facts_summary(sc_df, hc_df, combined_df):
    """Generate interesting summary statistics and fun facts"""
    print("\n\n🎉 FUN FACTS & INTERESTING DISCOVERIES")
    print("=" * 50)
    
    # Prepare the data using end-of-season snapshots
    sc_df = calculate_totals(sc_df)
    hc_df = calculate_totals(hc_df)
    combined_df = calculate_totals(combined_df)
    
    # Calculate total skill points allocated across all players
    # This gives us a sense of overall activity and engagement
    sc_skill_points = sc_df[sc_df['Type'] == 'Skill']['Total_Usage'].sum()
    hc_skill_points = hc_df[hc_df['Type'] == 'Skill']['Total_Usage'].sum()
    
    print(f"💪 Total skill points allocated (End of Season):")
    print(f"   Softcore: {sc_skill_points:,}")
    print(f"   Hardcore: {hc_skill_points:,}")
    print(f"   Combined: {sc_skill_points + hc_skill_points:,}")
    
    # Calculate total items used across all players
    # This shows economic activity and item circulation
    sc_items = sc_df[sc_df['Type'] != 'Skill']['Total_Usage'].sum()
    hc_items = hc_df[hc_df['Type'] != 'Skill']['Total_Usage'].sum()
    
    print(f"\n⚔️ Total items used (End of Season):")
    print(f"   Softcore: {sc_items:,}")
    print(f"   Hardcore: {hc_items:,}")
    print(f"   Combined: {sc_items + hc_items:,}")
    
    # Rank classes by total skill point usage (indicates popularity)
    class_popularity = combined_df[combined_df['Type'] == 'Skill'].groupby('Class')['Total_Usage'].sum().sort_values(ascending=False)
    print(f"\n🏛️ Most popular classes (by End of Season skill points):")
    for i, (char_class, total) in enumerate(class_popularity.items(), 1):
        print(f"   {i}. {char_class}: {total:,} skill points")
    
    # Compare the popularity of Runewords vs Unique items
    # This shows player preferences and game balance
    runeword_usage = combined_df[combined_df['Type'] == 'Runeword']['Total_Usage'].sum()
    unique_usage = combined_df[combined_df['Type'] == 'Unique']['Total_Usage'].sum()
    
    print(f"\n🔮 Runewords vs Uniques (End of Season):")
    print(f"   Runewords: {runeword_usage:,} uses")
    print(f"   Uniques: {unique_usage:,} uses")
    
    # Calculate and display which category is more popular
    if unique_usage > runeword_usage:
        ratio = unique_usage / runeword_usage
        print(f"   Uniques are {ratio:.1f}x more popular than runewords!")
    else:
        ratio = runeword_usage / unique_usage
        print(f"   Runewords are {ratio:.1f}x more popular than uniques!")

def main():
    """Main function that orchestrates the entire analysis"""
    print("🎮 PATH OF DIABLO - HARDCORE VS SOFTCORE ANALYSIS")
    print("Analyzing skill and item usage patterns across leagues")
    print("=" * 60)
    
    # Step 1: Load and prepare the data from CSV files
    sc_df, hc_df, combined_df = load_and_process_data()
    
    # Step 2: Run all the different analysis sections
    skills_df = analyze_skills(combined_df)           # Analyze skill usage patterns
    items_df = analyze_items(combined_df)             # Analyze item usage patterns
    analyze_trends(sc_df, hc_df)                      # Analyze trends over time
    
    # Step 3: Deep dive analyses for extra insights
    analyze_class_specialization(combined_df)        # Which classes are most specialized?
    analyze_mercenary_economy(combined_df)            # What do mercenaries wear?
    analyze_forgotten_skills(combined_df)             # Which skills are completely ignored?
    analyze_league_risk_tolerance(combined_df)        # Risk differences between SC/HC
    analyze_power_creep_indicators(combined_df)       # Signs of power creep in the meta
    
    # Step 4: Timeline analyses - track the entire season's evolution
    analyze_meta_evolution(sc_df, hc_df, combined_df) # How did the meta evolve month by month?
    analyze_seasonal_patterns(combined_df)            # What patterns emerged during the season?
    analyze_league_divergence_timeline(sc_df, hc_df)  # When did SC/HC preferences diverge most?
    analyze_meta_stability(combined_df)               # How stable was the meta?
    analyze_comeback_stories(combined_df)             # Dramatic rises and falls
    
    # Step 5: Generate summary statistics
    fun_facts_summary(sc_df, hc_df, combined_df)
    
    print("\n" + "=" * 60)
    print("Analysis complete! 🎉")

if __name__ == "__main__":
    main()