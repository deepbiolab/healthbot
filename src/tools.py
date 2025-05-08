"""
HealthBot Tools Module
This module defines the tools used by the HealthBot application.
"""

import os
from typing import Dict
from langchain_core.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv
load_dotenv()

# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(question: str) -> Dict:
    """
    Search the web for health information using Tavily.

    Args:
        question: The search query for health information

    Returns:
        Dict: Search results from Tavily
    """
    response = tavily_client.search(
        question,
        search_depth="advanced",
        include_domains=[
            "mayoclinic.org",
            "nih.gov",
            "who.int",
            "cdc.gov",
            "webmd.com",
            "healthline.com",
        ],
    )
    return response
