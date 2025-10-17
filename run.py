"""
Entry point to run the Kori POS Bot
Run this file from the project root directory
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main function
from src.main import main

if __name__ == "__main__":
    main()
