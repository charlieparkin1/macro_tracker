#!/usr/bin/env python3
import sys
import os

# Ensure Python finds the src folder
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.processing.scheduler import MacroScheduler


def main():
    print("Initializing Real-Time Macro Tracker...")
    print("Targeting: US CPI, US Unemployment, Eurozone Inflation")

    try:
        scheduler = MacroScheduler()
        scheduler.start()
    except KeyboardInterrupt:
        print("\nStopping Tracker... Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
