import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import pandas as pd
import os
import sys
import datetime
from scrape import (
    extract_steam_id, get_steam_username, get_steam_games,
    extract_username_from_url, should_update_database,
    get_game_info, match_games_with_compatibility
)

class MacLudusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MacLudus")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Set up the main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # URL input section
        url_frame = ttk.LabelFrame(main_frame, text="Steam Profile", padding="10")
        url_frame.pack(fill=tk.X, pady=5)

        ttk.Label(url_frame, text="Enter Steam Profile URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # API key input section
        api_key_frame = ttk.LabelFrame(main_frame, text="Steam API Key (Optional)", padding="10")
        api_key_frame.pack(fill=tk.X, pady=5)

        ttk.Label(api_key_frame, text="Enter Steam API Key:").pack(side=tk.LEFT, padx=5)
        self.api_key_entry = ttk.Entry(api_key_frame, width=50)
        self.api_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Add a help label for API key
        help_text = "If provided, the app will use the Steam API instead of web scraping.\nGet your API key at: https://steamcommunity.com/dev/apikey"
        ttk.Label(api_key_frame, text=help_text, foreground="gray").pack(side=tk.LEFT, padx=5)

        # Buttons section
        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.pack(fill=tk.X, pady=5)

        self.update_db_button = ttk.Button(button_frame, text="Update Database", command=self.update_database)
        self.update_db_button.pack(side=tk.LEFT, padx=5)

        self.check_button = ttk.Button(button_frame, text="Check Compatibility", command=self.check_compatibility)
        self.check_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(button_frame, text="Save Results", command=self.save_results, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Status section
        status_frame = ttk.Frame(main_frame, padding="5")
        status_frame.pack(fill=tk.X, pady=5)

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)

        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=20)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)

        # Data storage
        self.compatibility_data = None
        self.matched_games = None
        self.csv_filename = "macludus_compatible_games.csv"
        self.wiki_url = "https://www.applegamingwiki.com/wiki/M1_compatible_games_master_list"

        # Check if database exists and show last update time
        self.check_database_status()

    def check_database_status(self):
        """Check if the database exists and update the status with last update time"""
        if os.path.exists(self.csv_filename):
            last_update = datetime.datetime.fromtimestamp(os.path.getmtime(self.csv_filename))
            self.status_var.set(f"Database last updated: {last_update.strftime('%Y-%m-%d')}")
        else:
            self.status_var.set("Database not found. Please update the database.")

    def update_database(self):
        """Update the compatibility database from Apple Gaming Wiki"""
        self.set_busy_state(True)
        self.status_var.set("Updating database...")
        self.progress.start()

        # Run the update in a separate thread to keep the UI responsive
        threading.Thread(target=self._update_database_thread, daemon=True).start()

    def _update_database_thread(self):
        """Thread function to update the database"""
        try:
            games = get_game_info(self.wiki_url)
            if games:
                # Convert to DataFrame
                df = pd.DataFrame(games)

                # Save to CSV
                df.to_csv(self.csv_filename, index=False)

                # Try to save to Excel if openpyxl is available
                try:
                    import openpyxl
                    excel_filename = "macludus_compatible_games.xlsx"
                    df.to_excel(excel_filename, index=False)
                    self.root.after(0, lambda: self.status_var.set(
                        f"Database updated with {len(games)} games. Saved to CSV and Excel."))
                except ImportError:
                    self.root.after(0, lambda: self.status_var.set(
                        f"Database updated with {len(games)} games. Saved to CSV only."))

                # Store the compatibility data
                self.compatibility_data = games
            else:
                self.root.after(0, lambda: self.status_var.set(
                    "Failed to extract game information."))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to extract game information from Apple Gaming Wiki."))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error updating database: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error updating database: {str(e)}"))

        self.root.after(0, lambda: self.set_busy_state(False))
        self.root.after(0, lambda: self.progress.stop())
        self.root.after(0, self.check_database_status)

    def check_compatibility(self):
        """Check compatibility of games in the Steam profile"""
        steam_profile = self.url_entry.get().strip()
        if not steam_profile:
            messagebox.showwarning("Input Required", "Please enter a Steam profile URL.")
            return

        # Check if database exists
        if not os.path.exists(self.csv_filename):
            response = messagebox.askyesno(
                "Database Missing", 
                "Compatibility database not found. Would you like to update it now?")
            if response:
                self.update_database()
                return
            else:
                return

        self.set_busy_state(True)
        self.status_var.set("Checking compatibility...")
        self.progress.start()

        # Run the check in a separate thread
        threading.Thread(target=self._check_compatibility_thread, 
                         args=(steam_profile,), daemon=True).start()

    def _check_compatibility_thread(self, steam_profile):
        """Thread function to check compatibility"""
        try:
            # Load compatibility data if not already loaded
            if not self.compatibility_data:
                try:
                    compatibility_df = pd.read_csv(self.csv_filename)
                    self.compatibility_data = compatibility_df.to_dict('records')
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", f"Error loading compatibility data: {str(e)}"))
                    self.root.after(0, lambda: self.set_busy_state(False))
                    self.root.after(0, lambda: self.progress.stop())
                    return

            # Extract Steam ID from profile URL
            steam_id = extract_steam_id(steam_profile)
            if not steam_id:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Could not extract Steam ID from URL: {steam_profile}"))
                self.root.after(0, lambda: self.set_busy_state(False))
                self.root.after(0, lambda: self.progress.stop())
                return

            # Fetch the Steam username
            steam_username = get_steam_username(steam_id)
            if not steam_username:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Could not fetch username for Steam ID: {steam_id}. "
                    "The profile may be private or the Steam ID may be invalid."))
                self.root.after(0, lambda: self.set_busy_state(False))
                self.root.after(0, lambda: self.progress.stop())
                return

            # Update status with username
            self.root.after(0, lambda: self.status_var.set(
                f"Fetching games for {steam_username} (ID: {steam_id})..."))

            # Get API key if provided
            api_key = self.api_key_entry.get().strip()

            # Update status based on API key
            if api_key:
                self.root.after(0, lambda: self.status_var.set(
                    f"Using Steam API to fetch games for {steam_username}..."))
            else:
                self.root.after(0, lambda: self.status_var.set(
                    f"Using web scraping to fetch games for {steam_username}..."))

            # Fetch games from the Steam profile
            steam_games = get_steam_games(steam_id, api_key)
            if not steam_games:
                self.root.after(0, lambda: messagebox.showwarning(
                    "No Games Found", 
                    "No games found. The user's game list may be private or empty."))
                self.root.after(0, lambda: self.set_busy_state(False))
                self.root.after(0, lambda: self.progress.stop())
                return

            # Match Steam games with compatibility data
            self.matched_games = match_games_with_compatibility(steam_games, self.compatibility_data)

            # Display results
            self.root.after(0, lambda: self.display_results(steam_username, self.matched_games))

            # Enable save button
            self.root.after(0, lambda: self.save_button.config(state=tk.NORMAL))

            # Update status
            self.root.after(0, lambda: self.status_var.set(
                f"Found {len(steam_games)} games for {steam_username}. "
                f"Matched with compatibility data."))

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))

        self.root.after(0, lambda: self.set_busy_state(False))
        self.root.after(0, lambda: self.progress.stop())

    def display_results(self, username, matched_games):
        """Display the compatibility results in the text area"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, f"Compatibility information for {username}'s Steam games:\n")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        self.results_text.insert(tk.END, f"{'Game Name':<40} {'Native':<10} {'Rosetta 2':<10} "
                                        f"{'CrossOver':<10} {'Wine':<10} {'Parallels':<10}\n")
        self.results_text.insert(tk.END, "-" * 80 + "\n")

        for game in matched_games:
            self.results_text.insert(tk.END, 
                f"{game.get('name','')[:39]:<40}{game.get('native','Unknown'):<10}{game.get('rosetta_2','Unkown'):<10}"
                f"{game.get('crossover','Unknown'):<10}{game.get('wine','Unknown'):<10}{game.get('parallels','Unknown'):<10}\n")

        self.results_text.config(state=tk.DISABLED)

    def save_results(self):
        """Save the compatibility results to a CSV file"""
        if not self.matched_games:
            messagebox.showwarning("No Data", "No compatibility data to save.")
            return

        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Compatibility Results"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Save to CSV
            output_df = pd.DataFrame(self.matched_games)
            output_df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Results saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving results: {str(e)}")

    def set_busy_state(self, is_busy):
        """Set the UI state based on whether a task is running"""
        state = tk.DISABLED if is_busy else tk.NORMAL
        self.url_entry.config(state=state)
        self.api_key_entry.config(state=state)
        self.update_db_button.config(state=state)
        self.check_button.config(state=state)
        # Don't disable save button here, it's controlled separately

if __name__ == "__main__":
    root = tk.Tk()
    app = MacLudusGUI(root)
    root.mainloop()
