"""
HealthBot User Interface Module
This module handles the user interaction functions for the HealthBot application.
"""

import time

def display_text_to_user(text):
    """
    Display text to the user with a short delay to ensure rendering.
    
    Args:
        text: The text to display
    """
    print(text)
    time.sleep(1)  # wait for it to render before asking for input

def ask_user_for_input(input_description):
    """
    Ask the user for input with a given description.
    
    Args:
        input_description: The prompt to display to the user
        
    Returns:
        str: User's input response
    """
    response = input(input_description)
    return response