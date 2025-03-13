import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import time
import re
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

# Page configuration with custom theme
st.set_page_config(
    page_title="BasketballIQ - AI Analytics Assistant",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
  
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF4B4B;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #888888;
        margin-bottom: 30px;
    }
    .response-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #FF4B4B;
        color: #000000; /* Ensuring the text is clearly visible black */
        font-weight: 400; /* Medium weight for better readability */
    }
    .user-message {
        background-color: #e6f7ff;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #1890ff;
        color: #000000; /* Ensuring the text is clearly visible black */
        font-weight: 400; /* Medium weight for better readability */
    }
    .stButton>button {
        background-color: #FF4B4B;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #e6f7ff; /* Slightly darker red on hover */
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .sidebar-content {
        padding: 20px;
    }
    .download-button {
        background-color: #FF4B4B;
        color: white;
        text-color: white;
        padding: 10px 15px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
        border: none;
    }
    .download-button:hover {
        background-color: #45a049;
    }
</style>

""", unsafe_allow_html=True)

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.7
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = """You are BasketballIQ, an expert AI assistant specializing in basketball analytics, 
    player tracking data, coaching strategies, and sports science. Provide detailed, accurate information with references to 
    statistical metrics when relevant. Be friendly but professional, and format your responses in a clear, easy-to-read manner.
    Enhance answers with examples from NBA, WNBA, NCAA, and international basketball when appropriate. 
    
    IMPORTANT: All your recommendations and responses MUST be strictly related to basketball. If a question is not about basketball, 
    politely redirect the conversation back to basketball topics. When asked for recommendations, only provide basketball-related 
    recommendations."""

# Demo player stats for visualization
SAMPLE_PLAYERS = {
    "LeBron James": {
        "PPG": 25.7, "RPG": 7.3, "APG": 7.8, "FG%": 54, "3P%": 36, "FT%": 73,
        "games": [28, 22, 31, 25, 29, 26, 24, 30, 33, 27]
    },
    "Stephen Curry": {
        "PPG": 29.1, "RPG": 5.2, "APG": 6.3, "FG%": 48, "3P%": 42, "FT%": 91,
        "games": [32, 36, 29, 35, 28, 34, 31, 33, 30, 38]
    },
    "Giannis Antetokounmpo": {
        "PPG": 30.2, "RPG": 11.8, "APG": 5.6, "FG%": 61, "3P%": 30, "FT%": 68,
        "games": [34, 28, 32, 36, 29, 31, 38, 33, 30, 35]
    },
    "A'ja Wilson": {
        "PPG": 24.8, "RPG": 9.5, "APG": 2.3, "FG%": 52, "3P%": 33, "FT%": 85,
        "games": [26, 22, 28, 25, 30, 24, 27, 29, 31, 26]
    }
}

# Sample basketball analytics topics
ANALYTICS_TOPICS = [
    "Advanced offensive efficiency metrics", 
    "Defensive impact analysis", 
    "Shot selection optimization",
    "Player load management strategies",
    "In-game tactical adjustments",
    "Opponent scouting analysis",
    "Player development tracking",
    "Team chemistry quantification"
]

# Basketball-related keywords for content filtering
BASKETBALL_KEYWORDS = [
    'basketball', 'nba', 'wnba', 'ncaa', 'player', 'team', 'coach', 'shooting', 'defense', 'offense',
    'dribble', 'pass', 'rebound', 'assist', 'block', 'steal', 'turnover', 'court', 'foul', 'free throw',
    'jump shot', 'layup', 'dunk', 'three-pointer', 'pick and roll', 'fast break', 'zone defense',
    'man-to-man', 'basketball analytics', 'player efficiency', 'true shooting', 'effective field goal',
    'usage rate', 'defensive rating', 'offensive rating', 'plus-minus', 'box plus-minus', 'win shares',
    'vorp', 'per', 'pace', 'possession', 'basketball strategy', 'basketball statistics', 'basketball metrics'
]

# Configure API Key in sidebar
with st.sidebar:
    st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/889/889442.png", width=100)
    st.markdown("## BasketballIQ Settings")
    
    # API Key input with a toggle to show/hide
    show_api_key = st.checkbox("Show API Key Field", value=False)
    if show_api_key:
        API_KEY = st.text_input("Enter Gemini API Key:", placeholder="API-...", type="password")
        if API_KEY:
            try:
                genai.configure(api_key=API_KEY)
                st.success("API Key configured successfully!")
            except Exception as e:
                st.error(f"Error configuring API: {str(e)}")
    else:
        API_KEY = "AIzaSyDACGIyupAirbc50mJzTA9zN0SLWMTYvFc"  # Replace with your actual key in production
        try:
            genai.configure(api_key=API_KEY)
        except:
            pass
    
    # Model settings
    st.markdown("### Model Settings")
    st.session_state.temperature = st.slider("Temperature (Creativity)", min_value=0.0, max_value=1.0, value=st.session_state.temperature, step=0.1)
    
    # Custom system prompt
    st.markdown("### Expert System Prompt")
    st.session_state.system_prompt = st.text_area("Customize AI Behavior:", value=st.session_state.system_prompt, height=150)
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation"):
        st.session_state.chat_history = []
        st.success("Conversation cleared!")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Function to check if content is basketball-related
def is_basketball_related(content):
    content = content.lower()
    # Check if any basketball keyword is in the content
    for keyword in BASKETBALL_KEYWORDS:
        if keyword.lower() in content:
            return True
    return False

# Function to filter recommendations to ensure they're basketball-related
def filter_basketball_recommendations(response):
    # Check if it's a recommendation (looking for keyword patterns)
    recommendation_patterns = [
        r'recommend(?:ed|ation|ations)?',
        r'suggest(?:ed|ion|ions)?',
        r'advice',
        r'you (?:could|should|might) try',
        r'consider'
    ]
    
    is_recommendation = False
    for pattern in recommendation_patterns:
        if re.search(pattern, response.lower()):
            is_recommendation = True
            break
    
    # If it's a recommendation, check if it's basketball-related
    if is_recommendation and not is_basketball_related(response):
        # Replace with basketball-specific recommendation or redirect
        return (f"I'd like to focus our conversation on basketball. "
                f"For basketball-related recommendations, I suggest exploring topics like "
                f"player development metrics, advanced statistical analysis, or team strategy optimization. "
                f"What specific aspect of basketball would you like recommendations on?")
    
    return response

# Function to get response from Gemini with configurable parameters and basketball filter
def get_gemini_response(user_input, history):
    try:
        # Configure model - using gemini-1.0-pro (or gemini-1.5-pro) instead of gemini-pro
        model = genai.GenerativeModel(
            "gemini-1.5-flash",  # Using the free/available Gemini model
            generation_config={"temperature": st.session_state.temperature}
        )
        
        # Prepare the conversation context
        conversation_context = f"{st.session_state.system_prompt}\n\n"
        
        # Add chat history to provide context
        for entry in history:
            if entry["role"] == "user":
                conversation_context += f"User: {entry['content']}\n"
            else:
                conversation_context += f"Assistant: {entry['content']}\n"
        
        # Check if user input is basketball-related
        if not is_basketball_related(user_input):
            # Add a hint to keep responses basketball-focused
            conversation_context += "\nNOTE TO AI: Remember to only provide basketball-related information and recommendations. "
            conversation_context += "If the question is not about basketball, politely redirect the conversation to basketball topics.\n\n"
        
        # Add the current user query
        conversation_context += f"User: {user_input}\nAssistant: "
        
        # Generate response
        with st.spinner("BasketballIQ is analyzing your question..."):
            response = model.generate_content(conversation_context)
            time.sleep(0.5)  # Brief delay for UX
            
        # Apply basketball filter to the response, especially for recommendations
        filtered_response = filter_basketball_recommendations(response.text)
        return filtered_response
    except Exception as e:
        error_message = str(e)
        # Provide more helpful error messages
        if "model not found" in error_message.lower():
            return "Error: The specified model is not available. Using the free Gemini model requires a valid API key and access. Please check your API key or try using a different model that's available with your access level."
        else:
            return f"Error: {error_message}. Please check your API key and try again. If the problem persists, try using a different model version."

# Function to generate player stat visualization
def generate_player_stats(player_name):
    if player_name in SAMPLE_PLAYERS:
        player_data = SAMPLE_PLAYERS[player_name]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Basic stats bar chart
        basic_stats = ['PPG', 'RPG', 'APG']
        values = [player_data[stat] for stat in basic_stats]
        bars = ax1.bar(basic_stats, values, color=['#FF4B4B', '#1890FF', '#52C41A'])
        ax1.set_title(f"{player_name} - Basic Stats", fontsize=14)
        ax1.set_ylim(0, max(values) * 1.2)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f"{height:.1f}", ha='center', fontsize=11)
        
        # Shooting percentages
        shooting_stats = ['FG%', '3P%', 'FT%']
        shooting_values = [player_data[stat] for stat in shooting_stats]
        ax2.bar(shooting_stats, shooting_values, color=['#722ED1', '#13C2C2', '#FA8C16'])
        ax2.set_title(f"{player_name} - Shooting %", fontsize=14)
        ax2.set_ylim(0, 100)
        
        # Last 10 games trend line
        if 'games' in player_data:
            ax3 = fig.add_subplot(2, 1, 2)
            games = list(range(1, len(player_data['games']) + 1))
            ax3.plot(games, player_data['games'], marker='o', linestyle='-', color='#FF4B4B', linewidth=2)
            ax3.set_title(f"{player_name} - Last 10 Games (Points)", fontsize=14)
            ax3.set_xlabel('Game Number')
            ax3.set_ylabel('Points')
            ax3.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        return fig
    return None

# Function to create PDF from chat history
def create_chat_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a custom style for user messages
    user_style = ParagraphStyle(
        'UserStyle',
        parent=styles['Normal'],
        backColor=colors.lightblue,
        borderPadding=10,
        borderWidth=1,
        borderColor=colors.blue,
        borderRadius=5
    )
    
    # Create a custom style for assistant messages
    assistant_style = ParagraphStyle(
        'AssistantStyle',
        parent=styles['Normal'],
        backColor=colors.lightgrey,
        borderPadding=10,
        borderWidth=1,
        borderColor=colors.darkgrey,
        borderRadius=5
    )
    
    # Build the PDF content
    elements = []
    
    # Add title
    elements.append(Paragraph("BasketballIQ Chat History", title_style))
    elements.append(Spacer(1, 20))
    
    # Add date
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated on: {current_date}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Add chat history
    if not st.session_state.chat_history:
        elements.append(Paragraph("No chat history available.", normal_style))
    else:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                elements.append(Paragraph(f"<b>You:</b> {message['content']}", user_style))
            else:
                elements.append(Paragraph(f"<b>BasketballIQ:</b> {message['content']}", assistant_style))
            elements.append(Spacer(1, 10))
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Function to create a download link
def get_download_link(buffer, filename, link_text):
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-button">{link_text}</a>'
    return href

# Main page content
st.markdown("<h1 class='main-header'>🏀 BasketballIQ</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Your AI-powered basketball analytics assistant for data-driven insights</p>", unsafe_allow_html=True)

# Tab navigation
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Analytics Demo", "ℹ️ About"])

with tab1:
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"<div class='user-message'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='response-container'><strong>BasketballIQ:</strong> {message['content']}</div>", unsafe_allow_html=True)
    
    # Add download chat button
    if st.session_state.chat_history:
        pdf_buffer = create_chat_pdf()
        download_button = get_download_link(pdf_buffer, "basketballiq_chat.pdf", "📥 Download Chat as PDF")
        st.markdown(download_button, unsafe_allow_html=True)
    
    # Suggested questions
    if not st.session_state.chat_history:
        st.markdown("### 💡 Try asking:")
        cols = st.columns(3)
        suggested_questions = [
            "What advanced metrics best measure defensive impact?",
            "How can AI help optimize shot selection?",
            "Compare player tracking technologies in basketball",
            "Explain the four factors of basketball success",
            "What's the relationship between pace and efficiency?",
            "How do teams use data for in-game adjustments?"
        ]
        
        for i, question in enumerate(suggested_questions):
            if cols[i % 3].button(question):
                user_query = question
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                response = get_gemini_response(user_query, st.session_state.chat_history[:-1])
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    
    # User input
    with st.form(key="chat_form", clear_on_submit=True):
        user_query = st.text_area("💬 Ask a basketball analytics question:", placeholder="How can player tracking data improve defensive strategies?", height=100)
        submit_button = st.form_submit_button("Send Message")
        
    if submit_button and user_query:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        # Get AI response
        response = get_gemini_response(user_query, st.session_state.chat_history[:-1])
        
        # Add AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Force a rerun to display the updated chat
        st.rerun()

with tab2:
    st.markdown("### Basketball Analytics Visualization Demo")
    st.write("Explore sample player statistics and visualizations.")
    
    # Player selection and visualization
    selected_player = st.selectbox("Select Player for Analysis:", list(SAMPLE_PLAYERS.keys()))
    
    if selected_player:
        st.write(f"### {selected_player} Performance Analysis")
        fig = generate_player_stats(selected_player)
        if fig:
            st.pyplot(fig)
        
      # Advanced metrics explanation
        st.markdown("### Potential Advanced Metrics to Consider:")
        metrics_cols = st.columns(3)
        
        advanced_metrics = [
            ("True Shooting %", "Measures shooting efficiency accounting for FGs, 3Ps, and FTs"),
            ("Usage Rate", "Percentage of team plays used by a player while on the floor"),
            ("PER", "Player Efficiency Rating - overall rating of a player's per-minute productivity"),
            ("VORP", "Value Over Replacement Player - box score estimate of points per 100 possessions"),
            ("Defensive Win Shares", "Estimate of wins contributed by a player due to defense"),
            ("Net Rating", "Team point differential per 100 possessions with player on court")
        ]
        
        for i, (metric, desc) in enumerate(advanced_metrics):
            with metrics_cols[i % 3]:
                st.markdown(f"**{metric}**")
                st.markdown(f"<small>{desc}</small>", unsafe_allow_html=True)
    
    # Analytics Topics Explorer
    st.markdown("### Basketball Analytics Topics")
    st.write("Click on a topic to explore it further through the chatbot.")
    
    topic_cols = st.columns(4)
    for i, topic in enumerate(ANALYTICS_TOPICS):
        if topic_cols[i % 4].button(topic, key=f"topic_{i}"):
            # Add topic to chat history as a user query
            query = f"Explain {topic} in basketball and its importance"
            st.session_state.chat_history.append({"role": "user", "content": query})
            response = get_gemini_response(query, st.session_state.chat_history[:-1])
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            # Switch to chat tab
            try:
                st.experimental_set_query_params(tab="chat")
            except:
                # Fallback if experimental_set_query_params is deprecated
                pass
            st.rerun()

with tab3:
    st.markdown("### About BasketballIQ Assistant")
    st.write("""
    BasketballIQ is an AI-powered analytics assistant designed to help coaches, players, analysts, and basketball enthusiasts leverage data for better understanding of the game.
    
    **Capabilities:**
    - Answer questions about basketball analytics and statistics
    - Explain advanced metrics and their applications
    - Provide insights on player tracking data
    - Offer strategic recommendations based on data analysis
    - Visualize player and team performance metrics
    - Analyze game footage and extract actionable insights
    - Support data-driven decision making for coaches and teams
    """)
    
    # Features and benefits
    st.markdown("### Features & Benefits")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### For Coaches")
        st.write("""
        - Tactical decision support
        - Player rotation optimization
        - Opponent scouting insights
        - Practice planning recommendations
        - In-game adjustment suggestions
        """)
        
        st.markdown("#### For Players")
        st.write("""
        - Performance improvement insights
        - Skill development recommendations
        - Video analysis and feedback
        - Personalized training plans
        - Recovery and load management guidance
        """)
    
    with col2:
        st.markdown("#### For Analysts")
        st.write("""
        - Advanced statistical modeling
        - Predictive analytics tools
        - Custom report generation
        - Data visualization capabilities
        - Trend identification and analysis
        """)
        
        st.markdown("#### For Fans")
        st.write("""
        - Deeper understanding of the game
        - Access to insightful statistics
        - Player comparison tools
        - Fantasy basketball insights
        - Historical data exploration
        """)
    
    # Team and technology
    st.markdown("### Technology Stack")
    st.write("""
    BasketballIQ leverages cutting-edge AI and data analysis technology:
    
    - **Generative AI**: Powered by Google's Gemini model for natural language understanding and generation
    - **Data Visualization**: Interactive charts and graphs using Matplotlib and Streamlit
    - **Statistical Analysis**: Advanced basketball metrics computation
    - **User Interface**: Responsive and intuitive design via Streamlit
    """)
    
    # Contact information
    st.markdown("### Contact & Support")
    st.write("""
    For questions, feedback, or feature requests, please contact our team:
    
    - Email: support@basketballiq.ai
    - Twitter: @BasketballIQ_AI
    - GitHub: github.com/basketball-iq/app
    
    Version 1.0.0 | Last Updated: March 2025
    """)
    
    # Disclaimer
    st.markdown("### Disclaimer")
    st.write("""
    BasketballIQ is currently in beta. The analysis and insights provided should be used as a supplement to, not a replacement for, professional coaching and scouting. Statistical models and AI predictions have limitations and should be interpreted with appropriate context.
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>🏀 <b>BasketballIQ</b> | Powered by Gemini AI</div>
        <div>Made with ❤️ for basketball analytics enthusiasts</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# Add feedback mechanism
with st.expander("📝 Provide Feedback"):
    feedback_text = st.text_area("Share your thoughts on BasketballIQ:", placeholder="What did you like? What could be improved?")
    feedback_rating = st.slider("Rate your experience:", 1, 5, 5)
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! We'll use it to improve BasketballIQ.")
        # In a real application, you would store this feedback in a database