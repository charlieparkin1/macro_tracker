import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_event_alert(event_data: dict):
    """
    Prints a formatted alert to the terminal.
    Ref: dashboard_wireframe.txt (Colour Scheme)
    """
    # Mac Terminal Colors (ANSI Escape Codes)
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    classification = event_data.get("classification", "Neutral")

    # Determine Color based on classification
    if "Positive" in classification:
        color = GREEN
        icon = "🚀"  # Up rocket
    elif "Negative" in classification:
        color = RED
        icon = "🔻"  # Down triangle
    else:
        color = YELLOW
        icon = "Zap"  # Lightning

    print("\n" + "=" * 50)
    print(
        f"{BOLD}{color} {icon} MACRO EVENT DETECTED: {event_data.get('indicator')} {RESET}"
    )
    print("=" * 50)
    print(f"Date:      {event_data.get('date')}")
    print(f"Actual:    {BOLD}{event_data.get('actual')}%{RESET}")
    print(f"Expected:  {event_data.get('expected')}%")
    print(
        f"Surprise:  {color}{event_data.get('surprise')}{RESET} (Z-Score: {event_data.get('z_score')})"
    )
    print(f"Analysis:  {classification}")
    print("=" * 50 + "\n")
