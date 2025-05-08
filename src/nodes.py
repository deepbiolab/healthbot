"""
HealthBot Nodes Module
This module defines all the workflow nodes for the HealthBot application.
"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import END
from src.state import HealthBotState
from src.utils import display_text_to_user, ask_user_for_input
from src.tools import web_search
from src.models import initialize_model

# Initialize the language model
model = initialize_model()


def ask_health_topic(state: HealthBotState) -> HealthBotState:
    """
    Ask the patient what health topic they'd like to learn about.

    Args:
        state: Current state of the conversation

    Returns:
        Updated state with health topic and initial messages
    """
    display_text_to_user(
        "Welcome to HealthBot! I'm here to help you learn about health topics."
    )
    health_topic = ask_user_for_input(
        "What health topic or medical condition would you like to learn about? "
    )

    # Update state
    messages = [
        SystemMessage(
            content="You are a helpful healthcare assistant that provides accurate, patient-friendly information about health topics."
        ),
        HumanMessage(content=f"I want to learn about {health_topic}"),
    ]

    return {"health_topic": health_topic, "messages": messages}


def search_information(state: HealthBotState) -> HealthBotState:
    """
    Search for information about the health topic using Tavily.

    Args:
        state: Current state of the conversation

    Returns:
        Updated state with search results
    """
    health_topic = state["health_topic"]
    search_query = f"{health_topic} health information medical explanation"

    display_text_to_user(f"Searching for information about {health_topic}...")

    # Call Tavily search
    search_results = web_search.invoke(search_query)

    return {"search_results": search_results}


def summarize_information(state: HealthBotState) -> HealthBotState:
    """
    Summarize the search results into patient-friendly language.

    Args:
        state: Current state of the conversation

    Returns:
        Updated state with summary and updated message history
    """
    health_topic = state["health_topic"]
    search_results = state["search_results"]

    # Extract content from search results
    content = ""
    for result in search_results.get("results", []):
        content += f"Title: {result.get('title', '')}\n"
        content += f"Content: {result.get('content', '')}\n\n"

    # Create a prompt for summarization
    system_message = SystemMessage(
        content="""
    You are a healthcare educator who specializes in explaining medical concepts in simple, patient-friendly language.
    Summarize the provided information into 3-4 paragraphs that are easy to understand.
    Focus on key facts, symptoms, treatments, and preventive measures if applicable.
    Use simple language and avoid medical jargon when possible.
    If you need to use medical terms, provide a brief explanation.
    """
    )

    human_message = HumanMessage(
        content=f"""
    Please summarize the following information about {health_topic} in patient-friendly language:
    
    {content}
    """
    )

    # Generate summary
    ai_message = model.invoke([system_message, human_message])
    summary = ai_message.content

    return {
        "summary": summary,
        "messages": state["messages"] + [AIMessage(content=summary)],
    }


def present_summary(state: HealthBotState) -> HealthBotState:
    """
    Present the summarized information to the patient.

    Args:
        state: Current state of the conversation

    Returns:
        Unchanged state after displaying the summary
    """
    summary = state["summary"]

    display_text_to_user("\n=== HEALTH INFORMATION SUMMARY ===\n")
    display_text_to_user(summary)
    display_text_to_user("\n===================================\n")

    return state


def ready_for_quiz(state: HealthBotState) -> HealthBotState:
    """
    Ask if the patient is ready for a comprehension check.

    Args:
        state: Current state of the conversation

    Returns:
        Unchanged state after confirming readiness
    """
    ready = ask_user_for_input(
        "Are you ready for a quick comprehension check? (yes/no): "
    )

    if ready.lower() in ["yes", "y", "sure", "ok", "okay"]:
        return state
    else:
        # Give them more time to read
        display_text_to_user("Take your time. Let me know when you're ready.")
        ready_again = ask_user_for_input("Press Enter when you're ready to continue: ")
        return state


def generate_quiz(state: HealthBotState) -> HealthBotState:
    """
    Generate a quiz question based on the summary.

    Args:
        state: Current state of the conversation

    Returns:
        Updated state with quiz question
    """
    health_topic = state["health_topic"]
    summary = state["summary"]

    system_message = SystemMessage(
        content="""
    You are a healthcare educator creating a comprehension check question.
    Create ONE quiz question based ONLY on the information provided in the summary.
    The question should test understanding of a key concept from the summary.
    Make sure the answer can be found directly in the summary text.
    Don't provide the answer in the question.
    """
    )

    human_message = HumanMessage(
        content=f"""
    Please create one quiz question about {health_topic} based on this summary:
    
    {summary}
    """
    )

    # Generate quiz question
    ai_message = model.invoke([system_message, human_message])
    quiz_question = ai_message.content

    return {"quiz_question": quiz_question}


def present_quiz(state: HealthBotState) -> HealthBotState:
    """
    Present the quiz question to the patient.

    Args:
        state: Current state of the conversation

    Returns:
        Unchanged state after displaying the quiz
    """
    quiz_question = state["quiz_question"]

    display_text_to_user("\n=== COMPREHENSION CHECK ===\n")
    display_text_to_user(quiz_question)
    display_text_to_user("\n==========================\n")

    return state


def get_answer(state: HealthBotState) -> HealthBotState:
    """
    Get the patient's answer to the quiz question.

    Args:
        state: Current state of the conversation

    Returns:
        Updated state with user's answer
    """
    user_answer = ask_user_for_input("Your answer: ")

    return {"user_answer": user_answer}


def grade_answer(state: HealthBotState) -> HealthBotState:
    """
    Grade the patient's answer and provide feedback.

    Args:
        state: Current state of the conversation

    Returns:
        Updated state with grade and feedback
    """
    quiz_question = state["quiz_question"]
    user_answer = state["user_answer"]
    summary = state["summary"]

    system_message = SystemMessage(
        content="""
    You are a healthcare educator evaluating a patient's understanding.
    Grade the patient's answer to the quiz question.
    Provide a letter grade (A, B, C, D, or F) based on accuracy.
    Include specific feedback that references the original summary.
    Your feedback should include direct citations from the summary to reinforce learning.
    Be encouraging and supportive, even if the answer was not fully correct.
    """
    )

    human_message = HumanMessage(
        content=f"""
    Quiz Question: {quiz_question}
    
    Patient's Answer: {user_answer}
    
    Original Summary: {summary}
    
    Please grade this answer and provide feedback with citations from the summary.
    """
    )

    # Generate grade and feedback
    ai_message = model.invoke([system_message, human_message])
    grade_feedback = ai_message.content

    # Try to extract the letter grade from the feedback
    grade = "N/A"
    if "Grade: " in grade_feedback:
        grade = grade_feedback.split("Grade: ")[1].split("\n")[0].strip()
    elif grade_feedback[0].upper() in ["A", "B", "C", "D", "F"]:
        grade = grade_feedback[0].upper()

    return {"grade": grade, "feedback": grade_feedback}


def present_grade(state: HealthBotState) -> HealthBotState:
    """
    Present the grade and feedback to the patient.

    Args:
        state: Current state of the conversation

    Returns:
        Unchanged state after displaying the feedback
    """
    feedback = state["feedback"]

    display_text_to_user("\n=== FEEDBACK ===\n")
    display_text_to_user(feedback)
    display_text_to_user("\n===============\n")

    return state


def ask_continue(state: HealthBotState) -> HealthBotState:
    """
    Ask if the patient would like to learn about another health topic.

    Args:
        state: Current state of the conversation

    Returns:
        Updated state with continue_session flag
    """
    continue_choice = ask_user_for_input(
        "Would you like to learn about another health topic? (yes/no): "
    )

    continue_session = continue_choice.lower() in ["yes", "y", "sure", "ok", "okay"]

    return {"continue_session": continue_session}


def router(state: HealthBotState):
    """
    Route to either restart the flow or end the session.

    Args:
        state: Current state of the conversation

    Returns:
        String indicating next node or END
    """
    if state["continue_session"]:
        return "reset_state"
    else:
        return END


def reset_state(state: HealthBotState) -> HealthBotState:
    """
    Reset the state to start a new topic.

    Args:
        state: Current state of the conversation

    Returns:
        Reset state for a new session
    """
    display_text_to_user("Let's explore a new health topic!")

    # Reset all state values except messages (which will be reset in ask_health_topic)
    return {
        "health_topic": "",
        "search_results": None,
        "summary": "",
        "quiz_question": "",
        "user_answer": "",
        "grade": "",
        "feedback": "",
        "continue_session": True,
    }
