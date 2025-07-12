from dotenv import load_dotenv

from gui.app import ModerationApp
import tkinter as tk
import sys

if __name__ == "__main__":
    load_dotenv()
    try:
        app = ModerationApp()
        app.mainloop()
    except tk.TclError:
        print(
            "GUI initialization failed: a graphical display environment is "
            "required.",
            file=sys.stderr,
        )
        sys.exit(1)
