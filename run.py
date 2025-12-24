import sys
import os

# Add the current directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.cli.main import main

if __name__ == '__main__':
    main()
