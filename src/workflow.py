"""
HealthBot Workflow Module
This module defines the workflow graph for the HealthBot application.
"""

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from src.state import HealthBotState
from src.nodes import (
    ask_health_topic,
    search_information,
    summarize_information,
    present_summary,
    ready_for_quiz,
    generate_quiz,
    present_quiz,
    get_answer,
    grade_answer,
    present_grade,
    ask_continue,
    router,
    reset_state,
)


def create_workflow():
    """
    Create and configure the HealthBot workflow graph.

    Returns:
        tuple: Compiled workflow graph and memory saver instance
    """
    # Create the workflow graph
    workflow = StateGraph(HealthBotState)

    # Add nodes
    workflow.add_node("ask_health_topic", ask_health_topic)
    workflow.add_node("search_information", search_information)
    workflow.add_node("summarize_information", summarize_information)
    workflow.add_node("present_summary", present_summary)
    workflow.add_node("ready_for_quiz", ready_for_quiz)
    workflow.add_node("generate_quiz", generate_quiz)
    workflow.add_node("present_quiz", present_quiz)
    workflow.add_node("get_answer", get_answer)
    workflow.add_node("grade_answer", grade_answer)
    workflow.add_node("present_grade", present_grade)
    workflow.add_node("ask_continue", ask_continue)
    workflow.add_node("reset_state", reset_state)

    # Add edges
    workflow.add_edge(START, "ask_health_topic")
    workflow.add_edge("ask_health_topic", "search_information")
    workflow.add_edge("search_information", "summarize_information")
    workflow.add_edge("summarize_information", "present_summary")
    workflow.add_edge("present_summary", "ready_for_quiz")
    workflow.add_edge("ready_for_quiz", "generate_quiz")
    workflow.add_edge("generate_quiz", "present_quiz")
    workflow.add_edge("present_quiz", "get_answer")
    workflow.add_edge("get_answer", "grade_answer")
    workflow.add_edge("grade_answer", "present_grade")
    workflow.add_edge("present_grade", "ask_continue")

    # Add conditional edges
    workflow.add_conditional_edges(
        source="ask_continue",
        path=router,
        path_map={"reset_state": "ask_health_topic", END: END},
    )

    # Create memory saver for checkpointing
    memory = MemorySaver()

    # Compile the graph
    app = workflow.compile(checkpointer=memory)

    return app, memory
