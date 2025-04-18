import subprocess
import threading

def run_cli_in_background(args):
    """Run the CLI version in the background."""
    try:
        process = subprocess.Popen(
            ['python', 'main.py', '--cli'] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if stdout:
            print("CLI Output:", stdout.decode())
        if stderr:
            print("CLI Error:", stderr.decode())
    except Exception as e:
        print(f"Error running CLI in background: {e}")

if __name__ == "__main__":
    # Check if any arguments were provided
    if len(sys.argv) > 1:
        if sys.argv[1] == "--gui":
            # Launch the GUI version
            import tkinter as tk
            from gui import MacGameCompatibilityCheckerGUI

            # Start CLI in a separate thread
            cli_thread = threading.Thread(target=run_cli_in_background, args=(sys.argv[2:],))
            cli_thread.start()

            root = tk.Tk()
            app = MacGameCompatibilityCheckerGUI(root)
            root.mainloop()
        else:
            # Handle other arguments (e.g., CLI)
            ...
    else:
        # Default to GUI
        ...