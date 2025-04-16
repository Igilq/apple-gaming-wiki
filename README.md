# M1 Mac Game Compatibility Checker

This script helps Mac users check which games in their Steam library are compatible with Apple Silicon (M1/M2) Macs. It scrapes compatibility data from the [Apple Gaming Wiki](https://www.applegamingwiki.com/) and matches it with games in a Steam user's library.

## Features

- Automatically fetches and updates compatibility data from Apple Gaming Wiki
- Retrieves games from a Steam user's library using their profile URL
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
  - openpyxl (optional, for Excel export)

## Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install pandas requests beautifulsoup4
# Optional for Excel export
pip install openpyxl
```

## Usage

### Basic Usage

Run the script without arguments to be prompted for a Steam profile URL:

```bash
python scrape.py
```

### Command-line Arguments

The script supports several command-line arguments:

```bash
# Force update of the compatibility database
python scrape.py --update

# Check compatibility for Steam games (supports various URL formats)
python scrape.py --steam-profile https://steamcommunity.com/id/username
python scrape.py --steam-profile https://steamcommunity.com/profiles/76561198032608476
python scrape.py --steam-profile https://steamdb.info/calculator/76561198032608476/

# Specify custom output file
python scrape.py --output custom_filename.csv
```

### Workflow

1. The script will first check if the compatibility database needs updating (it auto-updates if older than 7 days)
2. If you didn't provide a Steam profile URL as an argument, it will prompt you to enter one
3. It will fetch and display the Steam username for confirmation
4. If you confirm it's the correct account, it will fetch games from the Steam profile
5. The script matches your games with the compatibility database
6. Results are displayed in the terminal and saved to a CSV file named after your Steam username

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

- The script uses public Steam APIs and doesn't require a Steam API key
- Game matching uses both exact and fuzzy matching to improve accuracy
- If a game isn't found in the compatibility database, it will be listed with "Unknown" status
- The Steam profile's game list must be public for the script to work

## Troubleshooting

- **"No games found"**: Make sure your Steam profile and game list are set to public
- **"Could not extract Steam ID"**: Check that you're using a valid Steam profile URL
- **Database update fails**: Check your internet connection and try again with the `--update` flag