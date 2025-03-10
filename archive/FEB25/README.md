# [Qords Info/Stats/Analytics for Path of Diablo](https://qordwasalreadytaken.github.io/pod-stats/Home.html)
Data analysis for the current PoD season

The Path of Diablo analytics site seems to have been orphaned, at least temporarily, leaving a gap in available data and trends on PoD builds. This is my attempt to provide similar information, and, although it's done in a different manner, the hope is that it helps users come to the same conclusions.

The original goal of this was not to directly replace the analytics site, but fill a hole until it (hopefully) comes back while also providing some information not included in that site. I really just wanted to look at all the bow and melee sorcs, count Shako's and Dangoons, and it turned into this.

The data used to create these is not real time, it's a snapshot in time that is refreshed on a regular basis.

# Feedback?
Let Qord know, Qord @ PoD Discord 

# To-do ++ community feedback
* Add sparation in long character lists to make it easier to see where one ends and the next begins
    * Done but not as helpful as it could be, borders are not full borders and leave some areas contiguous
    * Stretch divs all the way across instead of boxes?
        * Box text on Bong/Warpspear page
        * Stretch in Dashers
        * HR's in Non-zon
    * Go back to what it was before but add hr's?
* List of skills in a cluster/group could use better visibility, right now it's just a long list; not easy on the eyes
    * Line break every 5?
    * Columns?
    * list the paragraph style instead of a top-down list?
    * Smaller section with a scrollbar? If so then no reason to hide it behind a button
* Item displays for characters:
    * Add colors (blue for magic, gold for unique, etc.)
        * Item displays colored font done for class pages, but breaks the clustering for specialty pages
            * Working: Notazons, Dashadin, Chargers, Offensive Auras (but the title item is getting too...)
            * Not working: Unique arrows/bolts, Bong, Offensive Auras (need to fix title coloring)
    * Remove the "x1" from display
        * Not working: Chargers, Offensive Auras, Bong
* Skill display for characters, add icons for each character
    * Class pages done, need to do others
* Rotating Synth highlight in the fun facts?
* Charts
    * Some specialty pages still need adjustment
        * Pie Charts - Bong removed, it'll always be 50/50 so...
    * All scatter plots 
* Charge, non-zon - Change sort to class based groups and not skills
* Items - 
    * What exists for crafted, do that for magic and rare
    * Item counts by equipment slot, head body etc. breakdown of quality (rare, runeword, unique etc)

# To-do ++ community feedback - Completed
* List of skills in a cluster/group could use better visibility, right now it's just a long list; not easy on the eyes
    * Remove skills with zero points
    * Remove decimals
* Make character list consistent with Name: Level: Class: text and line breaks 
* Better way to present the "More detailed breakdown:" sections
    * Maybe give skills weight so, for example, a freezing pulse cluster presents itslef as a freezing pulse cluster so users don't have to read between the lines to see it
    * Weights added to MakeClassPages function; looks ok but will need care and feeding
* Make Armory links open in new tab instead of same tab
    * Done for SC and HC
* Move HC/SC toggle up to below home
    * Done for SC and HC
* Add timestamp
    * Added to main page pie chart and footer to others in SC
    * HC done?
* Add searches for crafted, synth
* Custom backgrounds
* Item displays for characters:
    * Add colors (blue for magic, gold for unique, etc.)
        * Item displays colored font done for class pages, but breaks the clustering for specialty pages
            * Working: Notazons, Dashadin, Chargers, Offensive Auras (but the title item is getting too...)
            * Not working: Unique arrows/bolts, Bong, Offensive Auras (need to fix title coloring)
    * Remove the "x1" from display
        * Not working: Chargers, Offensive Auras, Bong
* Pie charts
    * Class pages, some specialty pages done


# Known Issues to address
* Some item images in the pop up aren't displaying even though they work in the original twitch extension, looks like it's only the regex'd/text-replace ones? Can't be something I did, blame regex right? 
* Pie Charts not displayed properly, covered by labels
    * Removed most pie charts for now, they're still generated but the div to show them is commented out in the html's
        * Most are fixed, a few specialty pages still need help
* Hardcore had a low player base so the HC data includes a lot of low level characters, skewing data. Should it be floored at lvl 60? Some other level?
    * Hardcore floor changed to level 60, should it be higher still?
* The number of clusters (builds) to use was decided by cluster analysis, silhouette, and gap analysis, followed by just eyeballing them to see if the made sense. Can this be more automatic AND reliable?
* Reused names can cause duplicate character info to fall into multiple class buckets, fixing this has been manual; need to automate that so Zon's don't show up in sorc build breakdowns. 
    * Fix in place for SC, need to add to HC
    * Need to automate purge
* HC characters that have died don't have equipment, how best to address?
    * Changed armory quickview button to reflect "dead" status
    * Is that adequate?
* Item displays for characters:
    * Item count for Dashadin not right, removed.
    * Item displays good for class pages, but breaks the clustering for specialty pages

# Credits
Armory quickview pop ups are powered by the PoD Gear Twitch extension by Vinthian, Sizzles & Qord, adapted for use here by Qord

Thanks to Zardoz, GD, myang26, TheHornBlower, Sizzles

# About the process
Preface: I am not a programmer, if you are and you see room for improvement please let us know!
These html pages are generated by a series of python scripts, one for SC that contains all the functions that do all the work, another that contains it all for HC, and one that actually calls the functions contained in the other two. This setup allows for modular page creation, for example if only the HC Bong/Warpspear page needs updating then only that function needs to be run by uncommenting it and running the script. The downside to this is a LOT of redundant code, in some cases, to implement a change, that change has to be made in many places. This has resulted in a lot of complexity that can probably be avoided by someone who knows better.

While it would have been nice to just update the original page, lack of access to the source code and format of storage made this difficult. This presented the opportunity to do it a little different, using python to create static html pages was chosen because it's widely supported, cross platform, and allowed for great control over every aspect of the final product. This might all be possible in JS, but I was unable to do it in a way that I thought was acceptable. 

Current Folder Structure:
```bash
├Top Folder
├─ All the scripts
├─ SC folder
├── 8 subfolders, one for each class and one for ladder-all
├─ HC folder
├── 8 subfolders, one for each class and one for ladder-all
├─ PoD-Stats folder
├── archive folder - Need to standardize archive process and long term storage
│   ├── charts folder
│   │   ├── archived charts
│   ├── archived versions of the html files
├── armory folder
│   ├── Everything required to make the Armory Quickview pop-ups work (modified PoD Gear Twitch extention)
├── charts folder
│   ├── All the pie and scatter plot charts 
├── css folder
│   └── pod-stats.css
├── icons folder
│   ├── All skill icons
├── README.md
└── All of the individual html files (25-30 of them)
```
Running the get char data functions (GetAllCharData, GetClassCharData, GetAllhcCharData, GethcClassCharData) pull down json files and drops them in the relevant SC/HC subfolders.  
Running other get/make functions uses data in the relevant SC/HC subfolders to creates html files and charts, html files are saved inside PoD-Stats folder, and all pie and scatter charts are saved inside PoD-Stats\charts folder.  
Running the GitHubSync function pushes the contents of PoD-Stats folder up to github. (this functionality would need to be set by the user, this is not universal)

To execute these python files you will need to install python and these libraries:
pip install requests
pip install pandas
pip install scikit-learn
pip install plotly
pip install jinja2
