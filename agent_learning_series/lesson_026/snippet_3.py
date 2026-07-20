import math

def get_word_count(text: str) -> int:
    """Returns the number of words in a given text string."""
    return len(text.strip().split())

def calculate_hypotenuse(a: float, b: float) -> float:
    """Calculates the hypotenuse of a right-angled triangle."""
    return math.sqrt(a**2 + b**2)

# Map tools for dynamic routing
TOOLS_REGISTRY = {
    "get_word_count": get_word_count,
    "calculate_hypotenuse": calculate_hypotenuse
}