#!/usr/bin/env python3
import sys
import os

def show_help():
    """Display help information about the application"""
    print("M1 Mac Game Compatibility Checker")
    print("=================================")
    print("This application helps Mac users check which games in their Steam library")
    print("are compatible with Apple Silicon (M1/M2) Macs.")
    print("\nUsage:")
    print("  python main.py [options]")
    print("\nOptions:")
    print("  --gui           Launch the graphical user interface (default if no arguments)")
    print("  --cli           Launch the command-line interface")
    print("  --help, -h      Show this help message")
    print("\nFeatures:")
    print("  - Can use either the official Steam API (with API key) or web scraping")
    print("  - GUI includes a field for entering your Steam API key (optional)")
    print("  - CLI supports --api-key parameter for using the Steam API")
    print("\nFor CLI-specific options, run: python main.py --cli --help")

if __name__ == "__main__":
    # Check if any arguments were provided
    if len(sys.argv) > 1:
        # Process command line arguments
        if sys.argv[1] in ["--help", "-h"]:
            show_help()
        elif sys.argv[1] == "--cli":
            # Launch the CLI version by executing scrape.py with any additional arguments
            import scrape
            scrape.main()
        elif sys.argv[1] == "--gui":
            # Launch the GUI version
            import tkinter as tk
            from gui import MacGameCompatibilityCheckerGUI
            root = tk.Tk()
            app = MacGameCompatibilityCheckerGUI(root)
            root.mainloop()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        # No arguments provided, launch GUI by default
        try:
            import tkinter as tk
            from gui import MacGameCompatibilityCheckerGUI
            root = tk.Tk()
            app = MacGameCompatibilityCheckerGUI(root)
            root.mainloop()
        except ImportError as e:
            print("Error: Could not import tkinter. GUI mode is not available.")
            print(f"Error details: {e}")
            print("\nInstallation instructions for tkinter:")
            print("  - macOS: Install Python with tkinter using Homebrew:")
            print("    brew install python-tk")
            print("  - Linux (Debian/Ubuntu): sudo apt-get install python3-tk")
            print("  - Windows: Tkinter is included with standard Python installations")
            print("\nYou can still use the command-line interface:")
            print("python main.py --cli")
            sys.exit(1)
