"""
HealthBot State Module
This module defines the state class for the HealthBot application.
"""

from typing import Dict, Optional
from langgraph.graph import MessagesState

class HealthBotState(MessagesState):
    """
    State class for the HealthBot application.
    Inherits from MessagesState to maintain conversation history.
    """
    health_topic: str = ""
    search_results: Optional[Dict] = None
    summary: str = ""
    quiz_question: str = ""
    user_answer: str = ""
    grade: str = ""
    feedback: str = ""
    continue_session: bool = True