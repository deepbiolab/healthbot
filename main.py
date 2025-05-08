#!/usr/bin/env python3
"""
HealthBot Main Script
This script runs the HealthBot application from the command line.
"""

import os
import sys
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv

from src.workflow import create_workflow
from src.utils import display_text_to_user


def main():
    """
    Main function to run the HealthBot application.
    """
    # Load environment variables
    load_dotenv()
    # Check for required API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key.")
        sys.exit(1)

    if not os.getenv("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY not found in environment variables.")
        print("Please create a .env file with your Tavily API key.")
        sys.exit(1)

    # Create the workflow
    app, _ = create_workflow()

    # Configure the workflow
    config = RunnableConfig(
        recursion_limit=2000, configurable={"thread_id": "healthbot-session"}
    )

    # Initialize state
    initial_state = {"messages": []}

    # Display welcome message
    display_text_to_user("\n=== HealthBot: AI-Powered Patient Education System ===\n")
    display_text_to_user("Starting HealthBot...\n")

    try:
        # Run the HealthBot
        app.invoke(initial_state, config)

        # Display exit message
        display_text_to_user("\nThank you for using HealthBot! Stay healthy!\n")
    except KeyboardInterrupt:
        display_text_to_user("\n\nHealthBot session ended by user. Stay healthy!\n")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("Please check your API keys and internet connection.")


if __name__ == "__main__":
    main()
