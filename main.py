import sys

from core.app import main
from core.ui import C

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {C.GRAY}Exiting...{C.RESET}\n")
        sys.exit(0)
