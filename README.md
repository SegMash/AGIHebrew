# AGI Game Hebrew Translation Project

A complete Hebrew translation toolkit for Sierra's AGI Game including all game text, objects, inventory descriptions, and parser vocabulary.

## Overview

This project provides a complete translation workflow from English to Hebrew for AGI game, maintaining full compatibility with ScummVM while providing a native Hebrew gaming experience with proper right-to-left text support.

## Prerequisites

### Required Software
- **AGI Game** - Purchase from GOG.com
- **WinAGI** - For game file extraction and compilation
- **Python 3.x** - For running translation scripts. All tools tested with 3.13.
- **NSIS** - For creating the installer package
- **ScummVM Daily Build** - For testing and playing the translated game
- **AI Translation Service** - For automated translation assistance (ChatGPT, Claude, etc.)

### Directory Structure Setup
```
AGIHebrew/
├── clean/              # Original game files (backup)
├── work/               # Working directory for translation
├── tools/              # Translation scripts
├── output/             # Generated CSV and text files
├── nsis/               # Installer files and patches
└── README.md           # This documentation
```

## Quick Start Guide

### Phase 1: Setup and Preparation

#### 1. Game Setup
```bash
# Download for example, KQ1 from GOG.com and extract to 'clean' directory
# Copy all game files to 'work' directory for modification
# These files: LOGDIR, OBJECT, PICDIR, SNDDIR, VIEWDIR, VOL.*, WORDS
# Add clean and work dir as new games in scummvm and make sure they working as properly.
# Install NSIS
```

#### 2. Extract Game Content
- Import the working dir game in **WinAGI**.
- The import will extract all Logic files (Logic0.lgc, Logic1.lgc, etc.) to `src` dir.
- Fix WinAGI project if needed (remove Sound34 - Sound37)
- Ensure all resources are properly extracted
- Test "Compile Game" operation.
- Test the game using scummvm:
    - remove the "work dir" game.
    - add it again.
    - Currently the game is not recognized yet - choose the last game in the list.
    - Make sure it works fine.
    - This is the time to add "get" "drop" commands and to fix the logic itself.

#### 3. Prepare Translation Environment
First merge multilines messages. Note - in KQ1 when the game from GOG has no such lines and no free messages not in #message. So sometimes this step can be ignored. I recommend to run this step and to compare the src with the backup.

```bash
Example: python.exe .\tools\find_and_merge_multiline_prints.py --srcdir .\kq1_work\src --all --backup

```
This merges multi-line print statements into single lines for easier translation.

### Phase 2: Message Translation

#### 4. Export Game Messages
```bash
Example: python.exe .\tools\messages_export.py .\kq1_work\src output
```
Exports all in-game messages (#message, print, display, set.menu) to CSV format.

#### 5. Prepare for AI Translation - split the file
- Split the messages.csv file into chunks of ~200 lines
- This makes AI translation more manageable and accurate

```bash
Example: python.exe .\tools\split_file.py .\output\messages.csv --lines 200
```

#### 6. AI Translation Process
- Use the prompt in AI-prompt.txt
- In case the AI stopped proicessing, you can ask him to proceed with next file.


#### 7. Post AI Translation - merge the files.
```bash
Example: python.exe .\tools\merge_hebrew_files.py --srcdir .\output\messages_split\ --output .\output\messages_heb.csv
```

#### 8. Verify translation.
- Go over the file check it manually and fix translations if needed.
- If you see \" - replace with ""
- Remove the translation of game id. (Ex: KQ1)
- Replace the ">" with "<" (it's the prompt direction sign)
- Verify number of comma (should be no more than 4 (besides the commas inside "..."))
```bash
python.exe .\tools\check_csv_commas.py .\output\messages.csv
```
- If you find such rows - insert "..." surround the sentence.

#### 8.1 Upload csv to google drive
example:
```bash
python.exe .\tools\csv_xlsx_drive_v3.py --download --file-id tmpmjcpod_o.xlsx --output .\output\messages.csv
```

#### 8.2 Send link to google sheet to other people to review and fix.

#### 8.3 After all fixes - download the file
- Backup the original file
```bash
Move-Item .\output\messages.csv .\output\messages_backup.csv
```
- Get the file id by running this:
```bash
python.exe .\tools\csv_xlsx_drive_v3.py --list
```
- Download the new file
```bash
python.exe .\tools\csv_xlsx_drive_v3.py --download --file-id 1YspgPSt5l2l9-C8mfWQr0M24j8SefmpJ --output .\output\messages.csv
```

#### 8.4 Detect lines break in messages.csv - and fix manually
```bash
python.exe .\tools\check_csv_newlines.py .\output\messages.csv
```

#### 9. Import Translated Messages
```bash
python.exe .\tools\messages_import.py .\kq1_work\src  ./output/
```


#### 10. Verify Translation Completeness
```bash
python.exe .\tools\find_and_merge_multiline_prints.py --srcdir .\kq1_work\src\
```
- This scans for any remaining English text that needs translation.
- if you find missing translations - go back to the AI and ask to translate the missing in this part. - and then go back to step 7

### Phase 3: Game Compilation and Asset Review

#### 11. Compile and Test
- Compile the game using **WinAGI** (it's recommended to reopen the project)
- Copy the file agi-font-dos.bin from nsisFiles to your working game dir.
- Test basic functionality. In this stage you can wrote english commands and see hebrew messages!
- Look for any compilation errors
- If you edit logic files with WinAGI make sure your project is configured to encoded with Windows-1255, if not - edit the file with other editor and keep the encoding to be Windows-1255.



#### 12. Review Visual Assets
- Go through all views/pictures in WinAGI
- Identify any graphics with English text that need translation
- Edit graphics as needed and recompile

### Phase 4: Objects and Inventory

#### 13. Object Names
- First export objects to csv:
Example: 
```bash
python.exe .\tools\object_export.py .\kq1_work\ .\output\
```

- Translate objects using AI or manually. In the third line translate ? to ?

- Import the csv file
Example:
```bash
python.exe .\tools\object_import.py .\kq1_work\ .\output\
```

#### 14. Inventory Descriptions
- First using WinAGI search start index and end index of inventory objects.
- Now run this command example:
```bash
python.exe .\tools\read_viewdir_u24.py .\kq1_work --start 117 --end 141 --list-texts --output .\output\inventory_eng.txt
```

#### 15. Translate Inventory Descriptions
- Translate the generated inventory descriptions file. You can is AI.
- Save it for example under output\inventory_eng.txt.
- **Critical:** Hebrew sentences must be shorter than English equivalents!
- In order to check, run this script. Example:
```bash
python.exe .\tools\verify_translation_length.py .\output\inventory_eng.txt .\output\inventory_heb.txt
```


#### 16. Apply Inventory Translations
- Take a backup of your VOL.0 file.
- Now run for example:
```bash
python.exe .\tools\apply_inventory_descriptions_batch.py .\kq1_work --file .\output\inventory_heb.txt --start-index 117 --end-index 141
```
- Test again your game. take an object look at your inventory, look at the object.

### Phase 5: Parser and Vocabulary

#### 15. Export Game Vocabulary
- Example:
```bash
python.exe .\tools\words_export.py .\kq1_work\ .\output\
```

#### 16. Translate Vocabulary
- Use AI to translate the words.csv file
- Maintain verb/noun relationships
- Keep synonyms grouped properly


#### 17. Import Vocabulary
- Example
```bash
python.exe .\tools\words_import.py .\kq1_work\ .\output\
```
Verify that WORDS.TOK.EXTENDED file is created properly, and WORDS.TOK was changed.

### Phase 6: Distribution Package

#### 18. Generate Game Patches
Create binary patches for modified files:
Example:
```bash
GenPat.exe .\kq1_clean\VOL.0 .\kq1_work\VOL.0 .\nsisFiles\VOL.0.patch /r
GenPat.exe .\kq1_clean\OBJECT .\kq1_work\OBJECT .\nsisFiles\OBJECT.patch /r
GenPat.exe .\kq1_clean\LOGDIR .\kq1_work\LOGDIR .\nsisFiles\LOGDIR.patch /r
GenPat.exe .\kq1_clean\SNDDIR .\kq1_work\SNDDIR .\nsisFiles\SNDDIR.patch /r
GenPat.exe .\kq1_clean\PICDIR .\kq1_work\PICDIR .\nsisFiles\PICDIR.patch /r 
GenPat.exe .\kq1_clean\WORDS.TOK .\kq1_work\WORDS.TOK .\nsisFiles\WORDS.TOK.patch /r
GenPat.exe .\kq1_clean\VIEWDIR .\kq1_work\VIEWDIR .\nsisFiles\VIEWDIR.patch /r
```

#### 19. Copy WORDS.TOK.EXTENDED
```bash
# Copy additional required files to nsis directory
cp .\kq1_work\WORDS.TOK.EXTENDED .\nsisFiles\
```

#### 20. Edit Installer Configuration
- Update `installer.nsi` with correct paths and game information
- Verify all patch files are referenced correctly

#### 21. Build Installer
```bash
makensis.exe .\nsisFiles\installer.nsi
```
- As a result installer will be generated under your nsisFiles dir.

### Phase 7: ScummVM Integration

#### 23. Generate Detection Entry
```bash
# Calculate MD5 of translated LOGDIR file
(Get-FileHash -Algorithm MD5 .\kq1_work\LOGDIR).Hash.ToLower()
```

Create entry in ScummVM's `detection_table.h`:
- make sure to replace '<YOUR LOGDIR MD5 value>' with your MD5 value - lower case!
```cpp
// Example: King's Quest 1 Hebrew Translation
GAME_LVFPN("<game id lower case>", "", "logdir", "<YOUR LOGDIR MD5 value>", <size of LOGDIR in bytes>, Common::HE_ISR, 0x2917, GF_EXTCHAR, GID_KQ1, Common::kPlatformDOS, GType_V2, GAMEOPTIONS_DEFAULT),
```
- rebuild scummvm

### Phase 8: Testing and Release

#### 24. Quality Assurance
- Run the installer on clean game installation
- Run updated exe of scummvm and add the again again the clean game.
- Verify all text displays correctly in Hebrew
- Test save/load functionality with Hebrew names
- Check parser vocabulary works properly
- Test all game scenarios and endings

#### 25. Release Process
- Push detection_table.h changes to ScummVM repository
- Upload installer to GitHub releases
- Create release notes in Hebrew and English

#### 26. Community Announcement
- Post in "הרפתקה עברית" Facebook group
- Share on relevant gaming forums
- Update project documentation

## Technical Details

### File Encoding
- **Hebrew Text**: Windows-1255 encoding
- **Scripts**: UTF-8 with proper encoding handling
- **Game Files**: Original Sierra AGI format

### Translation Guidelines
- **Message Format**: Preserve original formatting codes
- **UI Constraints**: Hebrew text must fit original UI dimensions
- **Cultural Adaptation**: Adapt cultural references appropriately
- **Consistency**: Maintain terminology consistency throughout

### Patch System
- Uses NSIS VPatch for binary delta patches
- Only modified files are patched
- Original files are backed up automatically
- Uninstaller restores original English version

## Troubleshooting

### Common Issues

**Encoding Problems**
- Ensure all tools use Windows-1255 for Hebrew text
- Verify text editors save with correct encoding

**Text Overflow**
- Hebrew text may be longer than English
- Abbreviate translations when necessary
- Test in-game display before finalizing

**Parser Issues**
- Verify translated vocabulary maintains game logic
- Test command recognition with Hebrew input
- Check synonym relationships

**ScummVM Detection**
- Update detection tables for modified checksums
- Test with ScummVM daily builds
- Verify game variant is properly recognized

### Support Channels
- **Facebook**: "הרפתקה עברית" group
- **Discord**: Adventure game translation community
- **GitHub**: Technical issues and bug reports

## Credits

### Original Game
- **AGI Engine** reverse-engineered by ScummVM team
- Changes I did in the original game:
    * Change all "<any word>" to "anyword"
    * Remove the object 26 water. no such object in inventory descriptions. (VOL files)
    * instead of "get(water) - get full bucket and drop water bucket"



### Translation Tools
- Based on AGI reverse-engineering work - [adventurebrew team](https://github.com/adventurebrew/re-quest)
- Python scripts for automated translation workflow
- NSIS installer framework
- More scripts by Segev Mashraky.

## License

Translation tools and scripts are provided under MIT License. Original game content remains property of Sierra Entertainment/Activision. 

---

**Happy adventuring in Hebrew!**  
**!הרפתקה טובה בעברית**
