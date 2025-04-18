import pandas as pd
import requests
import re
import json
import os
import datetime
import time
from bs4 import BeautifulSoup


def extract_username_from_url(profile_url):
    """
    Extract username from a Steam profile URL.
    Returns the username part of the URL for use in filenames.
    Supports Steam Community URLs and SteamDB URLs.
    """
    # Check if it's a vanity URL
    vanity_match = re.search(r'steamcommunity\.com/id/([^/]+)', profile_url)
    if vanity_match:
        return vanity_match.group(1)

    # Check if it's a steamID64 URL
    steamid64_match = re.search(r'steamcommunity\.com/profiles/(\d+)', profile_url)
    if steamid64_match:
        return steamid64_match.group(1)

    # Check if it's a SteamDB URL
    steamdb_match = re.search(r'steamdb\.info/calculator/(\d+)', profile_url)
    if steamdb_match:
        return steamdb_match.group(1)

    # If no match, return a default name
    return "steam_user"

def should_update_database(csv_filename, update_threshold_days=7):
    """
    Check if the compatibility database needs updating.
    Returns True if the file doesn't exist or is older than the threshold.
    """
    # If file doesn't exist, it needs updating
    if not os.path.exists(csv_filename):
        return True

    # Check file age
    file_mod_time = os.path.getmtime(csv_filename)
    current_time = time.time()
    file_age_days = (current_time - file_mod_time) / (60 * 60 * 24)  # Convert seconds to days

    # If file is older than threshold, it needs updating
    return file_age_days > update_threshold_days

def extract_steam_id(profile_url):
    """
    Extract Steam ID from a Steam profile URL.
    Supports vanity URLs, direct steamID64 URLs, and SteamDB URLs.
    """
    # Check if it's a direct steamID64 URL
    steamid64_match = re.search(r'steamcommunity\.com/profiles/(\d+)', profile_url)
    if steamid64_match:
        return steamid64_match.group(1)

    # Check if it's a SteamDB URL
    steamdb_match = re.search(r'steamdb\.info/calculator/(\d+)', profile_url)
    if steamdb_match:
        return steamdb_match.group(1)

    # Check if it's a vanity URL
    vanity_match = re.search(r'steamcommunity\.com/id/([^/]+)', profile_url)
    if vanity_match:
        vanity_name = vanity_match.group(1)
        # Resolve vanity URL to steamID64
        # Note: This requires a Steam API key, which we don't have
        # For this implementation, we'll use a public endpoint that doesn't require an API key
        try:
            response = requests.get(f"https://steamcommunity.com/id/{vanity_name}?xml=1")
            if response.status_code == 200:
                steamid64_match = re.search(r'<steamID64>(\d+)</steamID64>', response.text)
                if steamid64_match:
                    return steamid64_match.group(1)
        except Exception as e:
            print(f"Error resolving vanity URL: {e}")

    return None

def normalize_game_name(name):
    """
    Normalize game name for better matching.
    Removes common prefixes, suffixes, and special characters.
    """
    # Convert to lowercase
    name = name.lower()

    # Remove special characters and replace with spaces
    name = re.sub(r'[^\w\s]', ' ', name)

    # Remove common prefixes and suffixes
    prefixes = ['the ', 'a ']
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]

    # Remove edition information
    editions = [
        ' edition', ' remastered', ' definitive', ' enhanced', ' complete',
        ' collection', ' game of the year', ' goty', ' deluxe', ' premium',
        ' standard', ' gold', ' ultimate', ' special', ' legendary'
    ]
    for edition in editions:
        name = name.replace(edition, '')

    # Remove year information (e.g., 2020, 2021)
    name = re.sub(r'\b\d{4}\b', '', name)

    # Remove roman numerals (e.g., I, II, III, IV, V)
    name = re.sub(r'\b[IVX]+\b', '', name)

    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name)

    # Trim whitespace
    name = name.strip()

    return name

def match_games_with_compatibility(steam_games, compatibility_data):
    """
    Match Steam games with compatibility data from Apple Gaming Wiki.
    Returns a list of dictionaries with game name and compatibility info.

    Matching algorithm:
    1. Try exact match on original name
    2. Try exact match on normalized name
    3. Try partial match on original name (with improved logic to avoid duplicate matches)
    4. Try partial match on normalized name (with improved logic to avoid duplicate matches)
    5. If no match found, add game with unknown compatibility
    """
    matched_games = []

    # Create a set to track which compatibility games have been matched
    matched_compatibility_indices = set()

    # Create a normalized version of compatibility data for better matching
    normalized_compatibility_data = []
    for game in compatibility_data:
        normalized_game = game.copy()
        normalized_game['normalized_name'] = normalize_game_name(game['name'])
        normalized_compatibility_data.append(normalized_game)

    # Process Steam games
    for steam_game in steam_games:
        normalized_steam_game = normalize_game_name(steam_game)

        # Skip empty game names
        if not steam_game.strip():
            continue

        # 1. Try exact match on original name
        found_match = False
        for i, game in enumerate(compatibility_data):
            if i in matched_compatibility_indices:
                continue  # Skip already matched games

            if game['name'].lower() == steam_game.lower():
                matched_games.append(game)
                matched_compatibility_indices.add(i)
                found_match = True
                break

        if found_match:
            continue

        # 2. Try exact match on normalized name
        for i, game in enumerate(normalized_compatibility_data):
            if i in matched_compatibility_indices:
                continue  # Skip already matched games

            if game['normalized_name'] == normalized_steam_game:
                matched_games.append({k: v for k, v in game.items() if k != 'normalized_name'})
                matched_compatibility_indices.add(i)
                found_match = True
                break

        if found_match:
            continue

        # 3. Try partial match on original name (prioritize more specific matches)
        best_match = None
        best_match_index = -1
        best_match_score = 0

        for i, game in enumerate(compatibility_data):
            if i in matched_compatibility_indices:
                continue  # Skip already matched games

            # Calculate a match score based on string similarity
            # Higher score means better match
            score = 0
            if steam_game.lower() in game['name'].lower():
                # If Steam game is a substring of compatibility game
                score = len(steam_game) / len(game['name'])
            elif game['name'].lower() in steam_game.lower():
                # If compatibility game is a substring of Steam game
                score = len(game['name']) / len(steam_game)

            if score > best_match_score:
                best_match_score = score
                best_match = game
                best_match_index = i

        if best_match and best_match_score > 0.5:  # Threshold to ensure good matches
            matched_games.append(best_match)
            matched_compatibility_indices.add(best_match_index)
            continue

        # 4. Try partial match on normalized name (prioritize more specific matches)
        best_match = None
        best_match_index = -1
        best_match_score = 0

        for i, game in enumerate(normalized_compatibility_data):
            if i in matched_compatibility_indices:
                continue  # Skip already matched games

            # Calculate a match score based on string similarity
            score = 0
            if normalized_steam_game in game['normalized_name']:
                # If normalized Steam game is a substring of normalized compatibility game
                score = len(normalized_steam_game) / len(game['normalized_name'])
            elif game['normalized_name'] in normalized_steam_game:
                # If normalized compatibility game is a substring of normalized Steam game
                score = len(game['normalized_name']) / len(normalized_steam_game)

            if score > best_match_score:
                best_match_score = score
                best_match = game
                best_match_index = i

        if best_match and best_match_score > 0.5:  # Threshold to ensure good matches
            matched_games.append({k: v for k, v in best_match.items() if k != 'normalized_name'})
            matched_compatibility_indices.add(best_match_index)
            continue

        # 5. No match found, add game with unknown compatibility
        matched_games.append({
            'name': steam_game,
            'url': '',
            'native': 'Unknown',
            'rosetta_2': 'Unknown',
            'crossover': 'Unknown',
            'wine': 'Unknown',
            'parallels': 'Unknown',
            'linux_arm': 'Unknown'
        })

    return matched_games

def get_steam_username(steam_id):
    """
    Get the username of a Steam user.
    Uses a public endpoint that doesn't require an API key.
    """
    try:
        # This endpoint is public and doesn't require an API key
        url = f"https://steamcommunity.com/profiles/{steam_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the username element
            username_element = soup.find('span', {'class': 'actual_persona_name'})
            if username_element:
                return username_element.text.strip()
            else:
                print("Could not find username on the profile page.")
        else:
            print(f"Failed to retrieve Steam profile. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching Steam username: {e}")

    return None

def get_steam_games_api(steam_id, api_key):
    """
    Get the list of games owned by a Steam user using the official Steam API.
    Requires a Steam API key.

    Args:
        steam_id (str): The Steam ID of the user
        api_key (str): The Steam API key

    Returns:
        list: A list of game names owned by the user
    """
    try:
        # Use the official Steam API to get the user's games
        url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={steam_id}&include_appinfo=1&format=json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if 'response' in data and 'games' in data['response']:
                games = data['response']['games']
                game_names = [game.get('name', '') for game in games if game.get('name')]
                print(f"Successfully extracted {len(game_names)} games using Steam API")
                return game_names
            else:
                print("No games found in the API response. The user's game list may be private.")
        else:
            print(f"Failed to retrieve Steam games via API. Status code: {response.status_code}")
            if response.status_code == 403:
                print("API key may be invalid or unauthorized.")
    except Exception as e:
        print(f"Error fetching Steam games via API: {e}")

    return []

def get_steam_games(steam_id, api_key=None):
    """
    Get the list of games owned by a Steam user.
    If an API key is provided, uses the official Steam API.
    Otherwise, tries the XML API first, then falls back to the JSON method if that fails.

    Args:
        steam_id (str): The Steam ID of the user
        api_key (str, optional): The Steam API key. Defaults to None.

    Returns:
        list: A list of game names owned by the user
    """
    # If API key is provided, use the official Steam API
    if api_key:
        games = get_steam_games_api(steam_id, api_key)
        if games:
            return games
        print("Steam API method failed, falling back to web scraping methods...")

    # Try the XML method first
    games = get_steam_games_xml(steam_id)
    if games:
        return games

    # If XML method fails, try the JSON method
    try:
        # This endpoint is public and doesn't require an API key
        url = f"https://steamcommunity.com/profiles/{steam_id}/games?tab=all"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Extract the JSON data from the page
            match = re.search(r'var rgGames = (\[.+?\]);', response.text, re.DOTALL)
            if match:
                games_json = match.group(1)
                try:
                    games = json.loads(games_json)
                    return [game.get('name', '') for game in games if game.get('name')]
                except json.JSONDecodeError as e:
                    print(f"Error parsing games JSON: {e}")
            else:
                # If the user's game list is private, we won't be able to extract it
                print("Could not find games list. The user's game list may be private.")
        else:
            print(f"Failed to retrieve Steam games. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching Steam games: {e}")

    return []

def get_steam_games_xml(steam_id):
    """
    Get the list of games owned by a Steam user using the XML API.
    This method works even for profiles that don't expose the JSON data.
    """
    try:
        # This endpoint is public and doesn't require an API key
        url = f"https://steamcommunity.com/profiles/{steam_id}/games?tab=all&xml=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Check if the response contains game information
            if '<games>' in response.text:
                # Extract game names and app IDs using regex
                game_names = re.findall(r'<name><!\[CDATA\[(.*?)\]\]></name>', response.text)
                app_ids = re.findall(r'<appID>(\d+)</appID>', response.text)

                # Create a dictionary to deduplicate games by app ID
                games_dict = {}
                for i in range(min(len(game_names), len(app_ids))):
                    app_id = app_ids[i]
                    name = game_names[i]
                    games_dict[app_id] = name

                # Convert back to a list of unique game names
                unique_games = list(games_dict.values())

                if unique_games:
                    print(f"Successfully extracted {len(unique_games)} unique games from XML API")
                    return unique_games
                else:
                    print("Could not extract game names from XML response.")
            else:
                print("XML response does not contain game information.")
        else:
            print(f"Failed to retrieve Steam games XML. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching Steam games XML: {e}")

    return []

def get_game_info(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table containing the game information
        # The table has ID 'table-listofgames' and classes 'pcgwikitable', 'template-infotable', 'sortable'
        table = soup.find('table', {'id': 'table-listofgames'})

        if not table:
            print("Could not find the games table on the page.")
            return None

        # Extract game information from the table
        games = []
        for row in table.find_all('tr')[1:]:  # Skip the header row
            # Get the game name from the row header (th)
            th_cell = row.find('th')
            if not th_cell:
                continue  # Skip rows without a header cell

            game_name = th_cell.text.strip()

            # Get the game URL if available
            game_url = ""
            game_link = th_cell.find('a')
            if game_link:
                game_url = "https://www.applegamingwiki.com" + game_link.get('href', '')

            # Get the compatibility ratings from the td cells
            td_cells = row.find_all('td')

            # Skip rows that don't have enough columns
            if len(td_cells) < 6:
                continue

            try:
                native = td_cells[0].text.strip() if len(td_cells) > 0 else "Unknown"
                rosetta_2 = td_cells[1].text.strip() if len(td_cells) > 1 else "Unknown"
                crossover = td_cells[2].text.strip() if len(td_cells) > 2 else "Unknown"
                wine = td_cells[3].text.strip() if len(td_cells) > 3 else "Unknown"
                parallels = td_cells[4].text.strip() if len(td_cells) > 4 else "Unknown"
                linux_arm = td_cells[5].text.strip() if len(td_cells) > 5 else "Unknown"

                # Skip entries where the game name is empty
                if not game_name:
                    continue

                game_info = {
                    'name': game_name,
                    'url': game_url,
                    'native': native,
                    'rosetta_2': rosetta_2,
                    'crossover': crossover,
                    'wine': wine,
                    'parallels': parallels,
                    'linux_arm': linux_arm
                }
                games.append(game_info)
            except Exception as e:
                print(f"Error processing row: {e}")
                continue

        return games
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None

def main():
    """
    Main function to handle command-line arguments and execute the appropriate actions.

    The script will:
    1. Auto-update the compatibility database if needed
    2. Prompt for a Steam profile URL if not provided
    3. Fetch and display the Steam username for confirmation
    4. Exit if the user says it's not the correct account
    5. Fetch games from the Steam profile using the Steam API
    6. Save results to a file named after the Steam user

    Usage examples:
    - Run with automatic prompts:
      python scrape.py

    - Force update compatibility database:
      python scrape.py --update

    - Check compatibility for Steam games (supports various URL formats):
      python scrape.py --steam-profile https://steamcommunity.com/id/username
      python scrape.py --steam-profile https://steamcommunity.com/profiles/76561198032608476
      python scrape.py --steam-profile https://steamdb.info/calculator/76561198032608476/

    - Specify custom output file:
      python scrape.py --output custom_filename.csv

    Note: The script uses the Steam API to fetch games, not SteamDB. SteamDB URLs are supported
    for extracting the Steam ID, but the actual game data comes from Steam's public API.
    """
    import argparse
    import sys
    import os.path

    parser = argparse.ArgumentParser(description='Fetch M1 Mac compatibility for Steam games')
    parser.add_argument('--update', action='store_true', help='Force update of the compatibility database')
    parser.add_argument('--steam-profile', type=str, help='Steam profile URL to check games compatibility')
    parser.add_argument('--output', type=str, help='Custom output file for compatibility results (CSV format)')
    parser.add_argument('--api-key', type=str, help='Steam API key (optional, will use web scraping if not provided)')

    args = parser.parse_args()

    # URL of the Apple Gaming Wiki page
    wiki_url = "https://www.applegamingwiki.com/wiki/M1_compatible_games_master_list"

    # CSV file to store/read compatibility data
    csv_filename = "../applegamingwiki/m1_compatible_games.csv"

    # Auto-update compatibility database if needed
    should_update = args.update or should_update_database(csv_filename)

    if should_update:
        print("Updating compatibility database from Apple Gaming Wiki...")
        try:
            games = get_game_info(wiki_url)
            if games:
                print(f"Successfully extracted information for {len(games)} games.")

                # Convert to DataFrame
                df = pd.DataFrame(games)

                # Save to CSV
                df.to_csv(csv_filename, index=False)
                print(f"Data saved to {csv_filename}")

                # Save to Excel (optional)
                try:
                    import openpyxl
                    excel_filename = "m1_compatible_games.xlsx"
                    df.to_excel(excel_filename, index=False)
                    print(f"Data also saved to {excel_filename}")
                except ImportError:
                    print("Excel export skipped. To enable, install openpyxl: pip install openpyxl")
                except Exception as e:
                    print(f"Error saving to Excel: {e}")
            else:
                print("Failed to extract game information. Will try to use existing database if available.")
        except Exception as e:
            print(f"Error updating database: {e}")
            print("Will try to use existing database if available.")
    else:
        print(f"Using existing compatibility database (last updated: {datetime.datetime.fromtimestamp(os.path.getmtime(csv_filename)).strftime('%Y-%m-%d')})")

    # Prompt for Steam profile URL if not provided
    steam_profile = args.steam_profile
    if not steam_profile:
        steam_profile = input("Enter Steam profile URL (e.g., https://steamcommunity.com/id/username): ")
        if not steam_profile:
            print("No Steam profile URL provided. Exiting.")
            sys.exit(1)

    # Check if compatibility database exists
    if not os.path.isfile(csv_filename):
        print(f"Compatibility database file '{csv_filename}' not found and could not be created.")
        print("Please check your internet connection and try again.")
        sys.exit(1)

    # Try to load compatibility data from CSV
    try:
        compatibility_df = pd.read_csv(csv_filename)
        compatibility_data = compatibility_df.to_dict('records')
        print(f"Loaded compatibility data for {len(compatibility_data)} games.")
    except Exception as e:
        print(f"Error loading compatibility data: {e}")
        print("The compatibility database file may be corrupted.")
        sys.exit(1)

    # Extract Steam ID from profile URL
    steam_id = extract_steam_id(steam_profile)
    if not steam_id:
        print(f"Could not extract Steam ID from URL: {steam_profile}")
        print("Please provide a valid Steam profile URL.")
        sys.exit(1)

    # Fetch the actual Steam username
    steam_username = get_steam_username(steam_id)
    if not steam_username:
        print(f"Could not fetch username for Steam ID: {steam_id}")
        print("The profile may be private or the Steam ID may be invalid.")
        sys.exit(1)

    # Ask for user confirmation
    print(f"Found Steam account: {steam_username} (ID: {steam_id})")
    confirmation = input("Is this the correct Steam account? (yes/no): ").strip().lower()
    if confirmation != "yes" and confirmation != "y":
        print("Exiting as requested.")
        sys.exit(0)

    # Use the actual Steam username for the output filename if available
    # Otherwise, fall back to extracting from the URL
    if steam_username:
        # Sanitize the username for use in filenames
        # Replace spaces with underscores and remove any characters that aren't allowed in filenames
        username = re.sub(r'[^\w\-\.]', '_', steam_username)
    else:
        username = extract_username_from_url(steam_profile)

    print(f"Fetching games for Steam user: {steam_username} (ID: {steam_id})")

    # Use API key if provided
    api_key = args.api_key
    if api_key:
        print("Using provided Steam API key to fetch games...")
    else:
        print("No Steam API key provided, using web scraping methods...")

    steam_games = get_steam_games(steam_id, api_key)

    if not steam_games:
        print("No games found. The user's game list may be private or empty.")
        sys.exit(1)

    print(f"Found {len(steam_games)} games in the Steam library.")

    # Match Steam games with compatibility data
    matched_games = match_games_with_compatibility(steam_games, compatibility_data)

    # Display compatibility information
    print("\nCompatibility information for Steam games:")
    print("-" * 80)
    print(f"{'Game Name':<40} {'Native':<10} {'Rosetta 2':<10} {'CrossOver':<10} {'Wine':<10} {'Parallels':<10}")
    print("-" * 80)

    for game in matched_games:
        print(f"{game['name'][:39]:<40} {game['native']:<10} {game['rosetta_2']:<10} {game['crossover']:<10} {game['wine']:<10} {game['parallels']:<10}")

    # Determine output filename
    output_file = args.output if args.output else f"{username}_compatibility.csv"

    # Save results to CSV
    try:
        output_df = pd.DataFrame(matched_games)
        output_df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
    except Exception as e:
        print(f"\nError saving results to {output_file}: {e}")

if __name__ == "__main__":
    main()
