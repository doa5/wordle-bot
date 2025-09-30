import re
from typing import Optional, Tuple


def parse_wordle_score(message: str) -> Optional[Tuple[int, int]]:
    """
    Parse a Wordle score from a message.
    
    Expected format:
    Wordle XXX Y/6
    or
    Wordle XXX X/6
    
    Args:
        message: The message text to parse
        
    Returns:
        Tuple of (wordle_number, score) or None if not a valid Wordle message
        Score is 1-6 for successful guesses, 7 for failed (X/6)
    """
    # Pattern to match Wordle results
    # Matches: "Wordle 123 4/6" or "Wordle 123 X/6"
    pattern = r'Wordle\s+(\d+)\s+([X1-6])/6'
    
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        wordle_number = int(match.group(1))
        score_str = match.group(2)
        
        if score_str.upper() == 'X':
            score = 7  # Failed attempt
        else:
            score = int(score_str)
        
        return (wordle_number, score)
    
    return None


def is_wordle_message(message: str) -> bool:
    """
    Check if a message contains a Wordle score.
    
    Args:
        message: The message text to check
        
    Returns:
        True if message contains a Wordle score, False otherwise
    """
    return parse_wordle_score(message) is not None
