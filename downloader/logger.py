class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def log(message, level="info"):
    colors = {
        "info": Color.BLUE,
        "success": Color.GREEN,
        "warn": Color.YELLOW,
        "error": Color.RED,
    }
    print(f"{colors.get(level, Color.BLUE)}{message}{Color.RESET}")
