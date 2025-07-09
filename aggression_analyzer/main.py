from dotenv import load_dotenv

from gui.app import ModerationApp

if __name__ == "__main__":
    load_dotenv()
    app = ModerationApp()
    app.mainloop()
