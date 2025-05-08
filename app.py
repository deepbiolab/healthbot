#!/usr/bin/env python3
"""
HealthBot Web Application
This script runs the HealthBot as a web application using Streamlit.
"""

import os
import time
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.state import HealthBotState
from src.workflow import create_workflow
from src.tools import web_search
from src.models import initialize_model

# Load environment variables
load_dotenv()

# Check for required API keys
if not os.getenv("OPENAI_API_KEY"):
    st.error("Error: OPENAI_API_KEY not found in environment variables.")
    st.stop()

if not os.getenv("TAVILY_API_KEY"):
    st.error("Error: TAVILY_API_KEY not found in environment variables.")
    st.stop()

# Initialize the model
model = initialize_model()

# Set page configuration
st.set_page_config(
    page_title="HealthBot - Patient Education System", page_icon="🏥", layout="centered"
)

# Initialize session state if needed
if "messages" not in st.session_state:
    st.session_state.messages = []

if "health_topic" not in st.session_state:
    st.session_state.health_topic = ""

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "quiz_question" not in st.session_state:
    st.session_state.quiz_question = ""
    
if "quiz_options" not in st.session_state:
    st.session_state.quiz_options = []
    
if "quiz_correct_answers" not in st.session_state:
    st.session_state.quiz_correct_answers = []

if "user_answer" not in st.session_state:
    st.session_state.user_answer = []

if "feedback" not in st.session_state:
    st.session_state.feedback = ""

if "state" not in st.session_state:
    st.session_state.state = "initial"  # Possible states: initial, searching, summarizing, quiz, feedback, completed


def reset_session():
    """Reset the session to start a new topic"""
    st.session_state.messages = []
    st.session_state.health_topic = ""
    st.session_state.summary = ""
    st.session_state.quiz_question = ""
    st.session_state.quiz_options = []
    st.session_state.quiz_correct_answers = []
    st.session_state.user_answer = []
    st.session_state.feedback = ""
    st.session_state.state = "initial"


# Display header
st.title("🏥 HealthBot")
st.subheader("AI-Powered Patient Education System")
st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initial state - Ask for health topic
if st.session_state.state == "initial":
    st.markdown("Welcome to HealthBot! I'm here to help you learn about health topics.")

    with st.form(key="topic_form"):
        topic = st.text_input(
            "What health topic or medical condition would you like to learn about?"
        )
        submit_topic = st.form_submit_button("Learn about this topic")

        if submit_topic and topic:
            st.session_state.health_topic = topic
            st.session_state.messages.append(
                {"role": "user", "content": f"I want to learn about {topic}"}
            )
            st.session_state.state = "searching"
            st.rerun()

# Searching state - Show searching progress
elif st.session_state.state == "searching":
    with st.chat_message("assistant"):
        st.write(f"Searching for information about {st.session_state.health_topic}...")

        # Add spinner to show progress
        with st.spinner("Searching medical databases..."):
            # Call Tavily search
            search_query = f"{st.session_state.health_topic} health information medical explanation"
            search_results = web_search.invoke(search_query)

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
            Please summarize the following information about {st.session_state.health_topic} in patient-friendly language:
            
            {content}
            """
            )

            # Generate summary
            ai_message = model.invoke([system_message, human_message])
            summary = ai_message.content

            # Store the summary
            st.session_state.summary = summary
            st.session_state.messages.append({"role": "assistant", "content": summary})
            st.session_state.state = "summarized"
            st.rerun()

# Summarized state - Show summary and ask if ready for quiz
elif st.session_state.state == "summarized":
    st.markdown("### Would you like to test your understanding with a quick quiz?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, I'm ready"):
            st.session_state.state = "generating_quiz"
            st.rerun()
    with col2:
        if st.button("No, let me read more"):
            st.info("Take your time reading the information above.")

# Generating quiz state
elif st.session_state.state == "generating_quiz":
    with st.spinner("Generating quiz question..."):
        # Create a multiple-choice quiz question
        system_message = SystemMessage(
            content="""
        You are a healthcare educator creating a multiple-choice quiz question.
        Create ONE multiple-choice question based ONLY on the information provided in the summary.
        The question should test understanding of a key concept from the summary.
        
        IMPORTANT: Your question MUST have at least 2 correct answers to make it a true multiple-choice question.
        
        Your response must be in JSON format with the following structure:
        {
            "question": "The question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answers": [0, 2],  # Indices of correct answers (0-based), MUST include at least 2 indices
            "explanation": "Explanation of why these are the correct answers"
        }
        
        Make sure all options are plausible but only the correct answers are truly accurate based on the summary.
        The question should be phrased as "Select all that apply" or similar wording to indicate multiple answers.
        """
        )

        human_message = HumanMessage(
            content=f"""
        Please create one multiple-choice quiz question (with multiple correct answers) about {st.session_state.health_topic} based on this summary:
        
        {st.session_state.summary}
        """
        )

        # Generate quiz question
        try:
            ai_message = model.invoke([system_message, human_message])
            quiz_data = json.loads(ai_message.content)
            
            # Ensure it's a multiple-choice question
            if len(quiz_data["correct_answers"]) < 2:
                raise ValueError("Not enough correct answers for a multiple-choice question")
            
            # Store the quiz components
            st.session_state.quiz_question = quiz_data["question"]
            st.session_state.quiz_options = quiz_data["options"]
            st.session_state.quiz_correct_answers = quiz_data["correct_answers"]
            st.session_state.quiz_explanation = quiz_data.get("explanation", "")
            
            st.session_state.state = "quiz"
            st.rerun()
        except Exception as e:
            # Fallback in case of JSON parsing error
            st.error(f"Error generating quiz: {str(e)}. Trying again...")
            time.sleep(2)
            st.rerun()

# Quiz state - Show quiz question and get answer
elif st.session_state.state == "quiz":
    st.markdown("### Comprehension Check")
    st.markdown(st.session_state.quiz_question)
    st.markdown("_(Select all that apply)_")
    
    options = st.session_state.quiz_options
    selected_options = []
    
    for i, option in enumerate(options):
        if st.checkbox(option, key=f"option_{i}"):
            selected_options.append(i)
    
    if st.button("Submit Answer"):
        st.session_state.user_answer = selected_options
        st.session_state.state = "grading"
        st.rerun()

# Grading state - Grade the answer and provide feedback
elif st.session_state.state == "grading":
    with st.spinner("Evaluating your answer..."):
        # Compare user's answer with correct answers
        user_answers = st.session_state.user_answer
        correct_answers = st.session_state.quiz_correct_answers
        
        # Convert to sets for comparison
        user_set = set(user_answers)
        correct_set = set(correct_answers)
        
        # Calculate score
        if user_set == correct_set:
            grade = "A"
            grade_text = "Excellent! Your answer is completely correct."
        elif len(user_set & correct_set) > 0 and user_set.issubset(correct_set):
            grade = "B"
            grade_text = "Good job! You identified some correct answers, but missed a few."
        elif len(user_set & correct_set) > 0:
            grade = "C"
            grade_text = "You got some answers right, but also selected some incorrect options."
        else:
            grade = "F"
            grade_text = "Your answer doesn't match the correct option(s). Let's review the information."
        
        # Format the correct answers for display
        correct_options = [st.session_state.quiz_options[i] for i in correct_answers]
        correct_list = "\n".join([f"- {option}" for option in correct_options])
        
        # Create feedback with proper markdown formatting
        feedback = f"""
### Grade: {grade}

{grade_text}

### The correct answer(s) were:
{correct_list}

### Explanation:
{st.session_state.quiz_explanation}

This information was covered in the summary about {st.session_state.health_topic}.
"""
        
        # Store the feedback
        st.session_state.feedback = feedback
        st.session_state.messages.append({"role": "assistant", "content": feedback})
        st.session_state.state = "feedback"
        st.rerun()

# Feedback state - Show feedback and ask if continue
elif st.session_state.state == "feedback":
    st.markdown("### Would you like to learn about another health topic?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, new topic"):
            reset_session()
            st.rerun()
    with col2:
        if st.button("No, exit"):
            st.session_state.state = "completed"
            st.rerun()

# Completed state - Show thank you message
elif st.session_state.state == "completed":
    st.success("Thank you for using HealthBot! Stay healthy!")

    if st.button("Start New Session"):
        reset_session()
        st.rerun()

# Add sidebar with information
with st.sidebar:
    st.header("About HealthBot")
    st.markdown(
        """
    HealthBot is an AI-powered patient education system designed to:
    
    - Provide reliable health information
    - Explain medical concepts in simple language
    - Test your understanding with quizzes
    - Give personalized feedback
    
    All information is sourced from reputable medical websites.
    """
    )

    st.markdown("---")

    if st.button("Reset Conversation"):
        reset_session()
        st.rerun()