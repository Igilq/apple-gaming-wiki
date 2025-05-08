from flask import Flask, request, jsonify
import pandas as pd
import os
import datetime
import sys
from scrape import (
    extract_steam_id, get_steam_username, get_steam_games,
    get_game_info, match_games_with_compatibility
)

app = Flask(__name__)

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = os.path.join(script_dir, "macludus_compatible_games.csv")
WIKI_URL = "https://www.applegamingwiki.com/wiki/M1_compatible_games_master_list"

@app.route('/database-status', methods=['GET'])
def database_status():
    """Check if the database exists and return its last update time."""
    if os.path.exists(CSV_FILENAME):
        last_update = datetime.datetime.fromtimestamp(os.path.getmtime(CSV_FILENAME))
        return jsonify({
            "exists": True,
            "last_updated": last_update.strftime('%Y-%m-%d')
        })
    else:
        return jsonify({
            "exists": False,
            "last_updated": None
        })

@app.route('/update-database', methods=['POST'])
def update_database():
    """Update the compatibility database from Apple Gaming Wiki."""
    try:
        games = get_game_info(WIKI_URL)
        if games:
            df = pd.DataFrame(games)
            df.to_csv(CSV_FILENAME, index=False)
            return jsonify({"message": "Database updated successfully", "game_count": len(games)})
        else:
            return jsonify({"error": "Failed to extract game information"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check-compatibility', methods=['POST'])
def check_compatibility():
    """Check compatibility of games in the Steam profile."""
    data = request.json
    steam_profile = data.get("steam_profile")
    api_key = data.get("api_key", None)

    if not steam_profile:
        return jsonify({"error": "Steam profile URL is required"}), 400

    if not os.path.exists(CSV_FILENAME):
        return jsonify({"error": "Compatibility database not found"}), 500

    try:
        compatibility_df = pd.read_csv(CSV_FILENAME)
        compatibility_data = compatibility_df.to_dict('records')

        steam_id = extract_steam_id(steam_profile)
        if not steam_id:
            return jsonify({"error": "Invalid Steam profile URL"}), 400

        # Get the Steam username
        steam_username = get_steam_username(steam_id)
        if not steam_username:
            return jsonify({"error": "Could not fetch username for the provided Steam ID"}), 400

        steam_games = get_steam_games(steam_id, api_key)
        if not steam_games:
            return jsonify({"error": "No games found in the Steam library"}), 404

        matched_games = match_games_with_compatibility(steam_games, compatibility_data)
        return jsonify({
            "matched_games": matched_games,
            "username": steam_username,
            "game_count": len(steam_games)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-results', methods=['POST'])
def save_results():
    """Save the compatibility results to a CSV file."""
    data = request.json
    matched_games = data.get("matched_games")
    file_path = data.get("file_path")

    # If no file path is provided, use a default path in the script directory
    if not file_path:
        file_path = os.path.join(script_dir, "compatibility_results.csv")

    if not matched_games:
        return jsonify({"error": "No data to save"}), 400

    try:
        df = pd.DataFrame(matched_games)
        df.to_csv(file_path, index=False)
        return jsonify({"message": f"Results saved to {file_path}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
