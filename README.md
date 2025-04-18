# M1 Mac Game Compatibility Checker

This application helps Mac users check which games in their Steam library are compatible with Apple Silicon (M1/M2) Macs. It scrapes compatibility data from the [Apple Gaming Wiki](https://www.applegamingwiki.com/) and matches it with games in a Steam user's library.

## Features

- User-friendly GUI interface
- Command-line interface for automation and scripting
- Automatically fetches and updates compatibility data from Apple Gaming Wiki
- Retrieves games from a Steam user's library using their profile URL
- Optional Steam API key support for more reliable game fetching
- Matches Steam games with compatibility information
- Shows compatibility status for different methods:
  - Native Apple Silicon support
  - Rosetta 2 compatibility
  - CrossOver compatibility
  - Wine compatibility
  - Parallels compatibility
  - Linux on ARM compatibility
- Saves results to a CSV file for easy reference

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - pandas
  - requests
  - beautifulsoup4
  - tkinter (included with most Python installations, required for GUI)
  - openpyxl (optional, for Excel export)

## Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install pandas requests beautifulsoup4
# Optional for Excel export
pip install openpyxl
```

3. Ensure tkinter is installed (required for GUI):

   - **macOS**: If you installed Python using Homebrew, you need to install tkinter separately:
     ```bash
     # For Python 3.12 and earlier:
     brew install python-tk

     # For Python 3.13:
     brew install python-tk@3.13
     ```

   - **Linux (Debian/Ubuntu)**:
     ```bash
     sudo apt-get install python3-tk
     ```

   - **Windows**: Tkinter is included with standard Python installations from python.org

## Usage

### Starting the Application

You can start the application using the main.py script:

```bash
# Launch with GUI (default)
python main.py

# Launch with GUI explicitly
python main.py --gui

# Launch with command-line interface
python main.py --cli

# Show help information
python main.py --help
```

### Using the GUI

The graphical interface provides an easy way to use the application:

1. Enter a Steam profile URL in the text field
2. (Optional) Enter your Steam API key in the API key field for more reliable game fetching
   - If you don't have a Steam API key, you can get one at https://steamcommunity.com/dev/apikey
   - If no API key is provided, the application will use web scraping methods
3. Click "Update Database" to fetch the latest compatibility data (if needed)
4. Click "Check Compatibility" to analyze the Steam library
5. View the results in the text area
6. Click "Save Results" to save the compatibility data to a CSV file

![GUI Screenshot](https://i.imgur.com/example.png) <!-- Replace with actual screenshot when available -->

### Using the Command-line Interface

The command-line interface supports several arguments:

```bash
# Force update of the compatibility database
python main.py --cli --update

# Check compatibility for Steam games (supports various URL formats)
python main.py --cli --steam-profile https://steamcommunity.com/id/username
python main.py --cli --steam-profile https://steamcommunity.com/profiles/76561198032608476
python main.py --cli --steam-profile https://steamdb.info/calculator/76561198032608476/

# Specify custom output file
python main.py --cli --output custom_filename.csv

# Use a Steam API key for more reliable game fetching
python main.py --cli --steam-profile https://steamcommunity.com/id/username --api-key YOUR_STEAM_API_KEY
```

You can also use the original script directly:

```bash
python scrape.py --help
```

### Workflow

1. The application will first check if the compatibility database needs updating (it auto-updates if older than 7 days)
2. If you didn't provide a Steam profile URL, you'll be prompted to enter one
3. It will fetch and display the Steam username for confirmation
4. The application matches your games with the compatibility database
5. Results are displayed and can be saved to a CSV file

## Output

The script generates a CSV file with the following columns:

- `name`: Game name
- `url`: Link to the game's page on Apple Gaming Wiki (if available)
- `native`: Native Apple Silicon support status
- `rosetta_2`: Compatibility with Rosetta 2
- `crossover`: Compatibility with CrossOver
- `wine`: Compatibility with Wine
- `parallels`: Compatibility with Parallels
- `linux_arm`: Compatibility with Linux on ARM

Compatibility statuses are typically one of:
- `Yes`: Confirmed working
- `No`: Confirmed not working
- `Partial`: Works with issues
- `Unknown`: No information available

## Notes

- The application can use either:
  - The official Steam API (if you provide an API key) - more reliable but requires registration
  - Web scraping methods (if no API key is provided) - works without registration but may be less reliable
- To get a Steam API key, visit https://steamcommunity.com/dev/apikey (requires a Steam account)
- Game matching uses both exact and fuzzy matching to improve accuracy
- If a game isn't found in the compatibility database, it will be listed with "Unknown" status
- The Steam profile's game list must be public for the application to work
- The GUI uses threading to keep the interface responsive during data fetching

## Troubleshooting

- **"No games found"**: Make sure your Steam profile and game list are set to public
- **"Could not extract Steam ID"**: Check that you're using a valid Steam profile URL
- **Database update fails**: Check your internet connection and try again with the "Update Database" button or `--update` flag
- **GUI doesn't start or "No module named '_tkinter'"**: This error occurs when tkinter is not properly installed. Follow the installation instructions in the Installation section:
  - For macOS: `brew install python-tk`
  - For Linux: `sudo apt-get install python3-tk`
  - For Windows: Reinstall Python and make sure to check the "tcl/tk and IDLE" option during installation
- **Long operations seem to freeze**: The GUI uses threading but may appear unresponsive during very long operations
