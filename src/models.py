"""
HealthBot Models Module
This module initializes the language models used by the HealthBot application.
"""

from langchain_openai import ChatOpenAI

def initialize_model(temperature: float = 0.2):
    """
    Initialize the language model with specified parameters.
    
    Args:
        temperature: Controls randomness in the model's output (default: 0.2)
        
    Returns:
        ChatOpenAI: Configured language model instance
    """
    return ChatOpenAI(temperature=temperature)