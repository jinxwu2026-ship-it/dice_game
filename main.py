"""Launch The King's Gambit from the project folder (Python 3.10 or newer).

Recommended GUI version: install the dependency, then start the window:
    python -m pip install -r requirements-gui.txt
    python main.py --gui

Complete five-battle CLI run (standard library only; no pygame required):
    python main.py --run

Use python3 instead of python on macOS/Linux. The GUI needs a local desktop
display and cannot run in Ed's execution environment. Keep the complete
the_kings_gambit package and assets folder beside this launcher.
"""

from the_kings_gambit.main import main

if __name__ == "__main__":
    main()
