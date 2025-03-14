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
import numpy as np
import random

# Page configuration with custom theme
st.set_page_config(
    page_title="BUZZER AI - AI Analytics Assistant",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    :root {
        --primary-color: #4338CA;
        --secondary-color: #3B82F6;
        --accent-color: #10B981;
        --background-color: #F8FAFC;
        --text-color: #1E293B;
    }
    
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        color: #4338CA;
        margin-bottom: 10px;
        padding: 10px 0;
        display: block;
        text-align: center;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        margin-bottom: 30px;
    }
    
    .response-container {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid var(--primary-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: var(--text-color);
        font-weight: 400;
    }
    
    .user-message {
        background-color: #F1F5F9;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid var(--secondary-color);
        box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.05);
        color: var(--text-color);
        font-weight: 400;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    
    .sidebar-content {
        display: none;
        padding: 20px;
        background-color: #FFFFFF;
        border-radius: 12px;
    }
    
    .download-button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 12px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        font-weight: 600;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .download-button:hover {
        background: linear-gradient(135deg, var(--secondary-color), var(--accent-color));
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }
    
    /* Enhance form inputs */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    
    .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    
    /* Custom styling for metrics */
    .css-1wivf9j {
        background-color: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.7
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = """You are BUZZER AI, an expert AI assistant specializing in basketball analytics, 
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
    },
     "Ramana": {
        "PPG": 27.8, "RPG": 7.5, "APG": 7.3, "FG%": 54, "3P%": 36, "FT%": 85,
         "games": [25, 30, 28, 27, 22, 29, 24, 31, 26, 33]
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
    st.markdown("## BUZZER AI Settings")
    
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
        API_KEY = "AIzaSyDx0SghM2jwsFKC2fmnFd_4borirwdlu94"  # Replace with your actual key in production
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
        with st.spinner("BUZZER AI is analyzing your question..."):
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
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    # Enhanced custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#FF4B4B'),
        alignment=1  # Center alignment
    )
    
    # Style for date and metadata
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=1  # Center alignment
    )
    
    # Custom style for user messages
    user_style = ParagraphStyle(
        'UserStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        backColor=colors.HexColor('#e6f7ff'),
        borderPadding=10,
        borderWidth=1,
        borderColor=colors.HexColor('#1890ff'),
        borderRadius=8,
        spaceAfter=15,
        spaceBefore=15,
        alignment=0  # Left alignment
    )
    
    # Custom style for assistant messages
    assistant_style = ParagraphStyle(
        'AssistantStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        backColor=colors.HexColor('#f8f9fa'),
        borderPadding=10,
        borderWidth=1,
        borderColor=colors.HexColor('#FF4B4B'),
        borderRadius=8,
        spaceAfter=15,
        spaceBefore=15,
        alignment=0  # Left alignment
    )
    
    # Build the PDF content
    elements = []
    
    # Add logo and title
    elements.append(Paragraph("🏀 BUZZER AI Chat History", title_style))
    
    # Add date and metadata
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"📅 Generated on: {current_date}", meta_style))
    elements.append(Spacer(1, 20))
    
    # Add chat history with message numbers
    if not st.session_state.chat_history:
        elements.append(Paragraph("No chat history available.", styles['Normal']))
    else:
        message_count = 1
        for message in st.session_state.chat_history:
            content = message['content'].replace('*', '')  # Remove asterisks
            if message["role"] == "user":
                elements.append(Paragraph(
                    f"{message_count}. 👤 <b>You:</b><br/>{content}", 
                    user_style
                ))
            else:
                elements.append(Paragraph(
                    f"{message_count}. 🤖 <b>BUZZER AI:</b><br/>{content}", 
                    assistant_style
                ))
            message_count += 1
    
    # Add footer with page numbers
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(letter[0]/2, 30, text)
        canvas.restoreState()
    
    # Add footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "🏀 Generated by BUZZER AI - Your AI Basketball Analytics Assistant",
        meta_style
    ))
    
    # Build the PDF with page numbers
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    buffer.seek(0)
    return buffer

# Function to create a download link
def get_download_link(buffer, filename, link_text):
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-button">{link_text}</a>'
    return href

# Main page content
st.markdown("<h1 class='main-header'>🏀 BUZZER AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Your AI-powered basketball analytics assistant for data-driven insights</p>", unsafe_allow_html=True)

# Tab navigation
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Analytics Demo", "ℹ️ About"])

with tab1:
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"<div class='user-message'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='response-container'><strong>BUZZER AI:</strong> {message['content']}</div>", unsafe_allow_html=True)
    
    # Add download chat button
    if st.session_state.chat_history:
        pdf_buffer = create_chat_pdf()
        download_button = get_download_link(pdf_buffer, "BUZZER AI_chat.pdf", "📥 Download Chat as PDF")
        st.markdown(download_button, unsafe_allow_html=True)
    
    # Suggested questions
    if not st.session_state.chat_history:
        st.markdown("### 💡 Try asking:")
        cols = st.columns(3)
        suggested_questions = [
            "How can I analyze my team's defensive efficiency?",
            "What are the key metrics for evaluating player performance?",
            "How to develop a data-driven practice plan?",
            "What stats best predict future player success?",
            "How to use analytics for game-time decisions?",
            "What's the impact of rest days on player performance?"
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
    st.markdown("### 🏀 Elite Player Performance Hub")
    
    # Player Management Buttons
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("➕ Add New Player"):
            st.session_state.show_add_player_form = True
    with col2:
        if 'custom_players' in st.session_state and st.session_state.custom_players:
            player_to_remove = st.selectbox(
                "Select player to remove:",
                options=list(st.session_state.custom_players.keys()),
                key="remove_player"
            )
            if st.button("🗑️ Remove Player"):
                if player_to_remove in st.session_state.custom_players:
                    del st.session_state.custom_players[player_to_remove]
                    st.success(f"✅ Player {player_to_remove} removed successfully!")
                    st.rerun()
    
    # Add Player Form with Validation
    if 'show_add_player_form' in st.session_state and st.session_state.show_add_player_form:
        st.markdown("### 📝 Add New Player")
        with st.form("add_player_form"):
            # Basic Info
            col1, col2 = st.columns(2)
            with col1:
                new_player_name = st.text_input("Player Name*", help="Required field")
            with col2:
                player_position = st.selectbox("Position*", ["Guard", "Forward", "Center"], help="Required field")
            
            # Stats Input
            st.markdown("#### Player Statistics")
            stat_cols = st.columns(3)
            
            with stat_cols[0]:
                new_ppg = st.number_input("Points Per Game (PPG)*", min_value=0.0, max_value=50.0, value=0.0, help="Required field")
                new_rpg = st.number_input("Rebounds Per Game (RPG)*", min_value=0.0, max_value=25.0, value=0.0, help="Required field")
            
            with stat_cols[1]:
                new_apg = st.number_input("Assists Per Game (APG)*", min_value=0.0, max_value=15.0, value=0.0, help="Required field")
                new_fg_pct = st.number_input("Field Goal % (FG%)*", min_value=0.0, max_value=100.0, value=0.0, help="Required field")
            
            with stat_cols[2]:
                new_3p_pct = st.number_input("3-Point % (3P%)*", min_value=0.0, max_value=100.0, value=0.0, help="Required field")
                new_ft_pct = st.number_input("Free Throw % (FT%)*", min_value=0.0, max_value=100.0, value=0.0, help="Required field")
            
            # Last 10 Games Performance
            st.markdown("#### Last 10 Games Performance*")
            st.caption("Enter points scored in the last 10 games")
            games_cols = st.columns(5)
            last_10_games = []
            
            for i in range(10):
                with games_cols[i % 5]:
                    game_points = st.number_input(f"Game {i+1}", min_value=0, max_value=100, key=f"game_{i}", help="Required field")
                    last_10_games.append(game_points)
            
            # Submit Button with Validation
            submitted = st.form_submit_button("Add Player")
            
            if submitted:
                # Validate all required fields
                validation_failed = False
                error_messages = []
                
                if not new_player_name:
                    error_messages.append("Player Name is required")
                    validation_failed = True
                
                if new_ppg == 0 and new_rpg == 0 and new_apg == 0:
                    error_messages.append("At least one statistical category (PPG, RPG, APG) must have a value greater than 0")
                    validation_failed = True
                
                if all(game == 0 for game in last_10_games):
                    error_messages.append("Please enter at least one game performance")
                    validation_failed = True
                
                if validation_failed:
                    for error in error_messages:
                        st.error(error)
                else:
                    # Initialize session state for custom players if not exists
                    if 'custom_players' not in st.session_state:
                        st.session_state.custom_players = {}
                    
                    # Add new player to custom players
                    st.session_state.custom_players[new_player_name] = {
                        "PPG": new_ppg,
                        "RPG": new_rpg,
                        "APG": new_apg,
                        "FG%": new_fg_pct,
                        "3P%": new_3p_pct,
                        "FT%": new_ft_pct,
                        "games": last_10_games,
                        "position": player_position
                    }
                    
                    st.success(f"✅ Player {new_player_name} added successfully!")
                    st.session_state.show_add_player_form = False
                    st.rerun()
    
    # Combine sample and custom players for selection
    all_players = {**SAMPLE_PLAYERS}
    if 'custom_players' in st.session_state:
        all_players.update(st.session_state.custom_players)
    
    # Create tabs for different analysis views
    analysis_tabs = st.tabs(["📊 Player Stats", "🔄 Head-to-Head", "🎯 Shot Analysis", "📈 Performance Tracker", "🎮 Game Strategy"])
    
    with analysis_tabs[0]:
        st.subheader("Player Performance Dashboard")
        
        # Updated player selection to include custom players
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_player = st.selectbox("Select Player:", list(all_players.keys()), key="stats_player")
            
            # Player card with position if available
            player_data = all_players[selected_player]
            position_text = f"\nPosition: {player_data.get('position', 'N/A')}" if 'position' in player_data else ""
            
            st.markdown(f"""
            <div style='padding: 20px; border-radius: 10px; border: 2px solid #FF4B4B; background-color: white;'>
                <h3 style='color: #FF4B4B;'>{selected_player}</h3>
                <p>Career Highlights{position_text}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if selected_player:
                player_data = all_players[selected_player]
                
                # Elite Skills Rating
                skills_cols = st.columns(5)
                skills = {
                    "Scoring": min((player_data["PPG"] / 35) * 100, 100),
                    "Playmaking": min((player_data["APG"] / 12) * 100, 100),
                    "Rebounding": min((player_data["RPG"] / 15) * 100, 100),
                    "Efficiency": min((player_data["FG%"] / 65) * 100, 100),
                    "Consistency": max(min(100 - (np.std(player_data["games"]) / max(np.mean(player_data["games"]), 0.001) * 100), 100), 0)
                }
                
                for i, (skill, rating) in enumerate(skills.items()):
                    with skills_cols[i]:
                        st.markdown(f"**{skill}**")
                        # Ensure progress value is between 0 and 1
                        progress_value = max(min(rating/100, 1.0), 0.0)
                        st.progress(progress_value)
                        st.write(f"{rating:.0f}")
        
        # Performance Metrics Dashboard
        st.markdown("### 📊 Advanced Performance Metrics")
        metric_cols = st.columns(4)
        
        # Calculate advanced metrics
        ts_percentage = (player_data["PPG"] / (2 * (player_data["FG%"]/100 * 10 + player_data["FT%"]/100 * 4))) * 100
        versatility = (player_data["PPG"]/30 + player_data["RPG"]/10 + player_data["APG"]/10) * 10
        impact_score = (player_data["PPG"] * 0.4 + player_data["RPG"] * 0.3 + player_data["APG"] * 0.3)
        efficiency = (player_data["FG%"] + player_data["3P%"] + player_data["FT%"]) / 3
        
        with metric_cols[0]:
            st.metric("Impact Score", f"{impact_score:.1f}", "Overall Impact")
        with metric_cols[1]:
            st.metric("True Shooting", f"{ts_percentage:.1f}%", "Scoring Efficiency")
        with metric_cols[2]:
            st.metric("Versatility", f"{versatility:.1f}", "All-Around Game")
        with metric_cols[3]:
            st.metric("Efficiency", f"{efficiency:.1f}%", "Shooting Success")
        
        # Performance Visualization
        st.markdown("### 📈 Performance Breakdown")
        fig = generate_player_stats(selected_player)
        if fig:
            st.pyplot(fig)
    
    with analysis_tabs[1]:
        st.subheader("Head-to-Head Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            player1 = st.selectbox("Select First Player:", list(all_players.keys()), key="p1")
        with col2:
            player2 = st.selectbox("Select Second Player:", list(all_players.keys()), key="p2")
        
        if player1 and player2:
            # Create comparison metrics
            comparison_data = {
                "Metrics": ["Points", "Rebounds", "Assists", "FG%", "3P%", "FT%"],
                player1: [all_players[player1][stat] for stat in ["PPG", "RPG", "APG", "FG%", "3P%", "FT%"]],
                player2: [all_players[player2][stat] for stat in ["PPG", "RPG", "APG", "FG%", "3P%", "FT%"]]
            }
            
            df = pd.DataFrame(comparison_data)
            
            # Display comparison chart
            st.markdown("### 📊 Statistical Comparison")
            st.bar_chart(df.set_index("Metrics"))
            
            # Show head-to-head insights
            st.markdown("### 🔍 Key Matchup Insights")
            insights_cols = st.columns(3)
            
            with insights_cols[0]:
                scoring_diff = all_players[player1]["PPG"] - all_players[player2]["PPG"]
                st.metric("Scoring Advantage", 
                         f"{abs(scoring_diff):.1f} PPG",
                         f"{'Player 1' if scoring_diff > 0 else 'Player 2'} leads")
            
            with insights_cols[1]:
                efficiency_1 = (all_players[player1]["FG%"] + all_players[player1]["3P%"]) / 2
                efficiency_2 = (all_players[player2]["FG%"] + all_players[player2]["3P%"]) / 2
                st.metric("Shooting Efficiency", 
                         f"{abs(efficiency_1 - efficiency_2):.1f}%",
                         f"{'Player 1' if efficiency_1 > efficiency_2 else 'Player 2'} more efficient")
            
            with insights_cols[2]:
                impact_1 = all_players[player1]["PPG"] + all_players[player1]["RPG"] + all_players[player1]["APG"]
                impact_2 = all_players[player2]["PPG"] + all_players[player2]["RPG"] + all_players[player2]["APG"]
                st.metric("Overall Impact", 
                         f"{abs(impact_1 - impact_2):.1f}",
                         f"{'Player 1' if impact_1 > impact_2 else 'Player 2'} has higher impact")
    
    with analysis_tabs[2]:
        st.subheader("Shot Distribution Analysis")
        selected_player = st.selectbox("Select Player:", list(all_players.keys()), key="shot_analysis")
        
        if selected_player:
            player_data = all_players[selected_player]
            
            # Create shot distribution visualization
            st.markdown("### 🎯 Shot Selection Breakdown")
            shot_cols = st.columns(2)
            
            with shot_cols[0]:
                # Shot type distribution
                shot_types = {
                    "3-Pointers": player_data["3P%"],
                    "Mid-Range": 45,  # Sample data
                    "Paint": 65,      # Sample data
                    "Free Throws": player_data["FT%"]
                }
                
                # Create shot type chart
                fig, ax = plt.subplots(figsize=(8, 8))
                colors = ['#FF4B4B', '#1890FF', '#52C41A', '#722ED1']
                ax.pie(shot_types.values(), labels=shot_types.keys(), colors=colors, autopct='%1.1f%%')
                ax.set_title(f"{selected_player}'s Shot Distribution")
                st.pyplot(fig)
            
            with shot_cols[1]:
                st.markdown("### 📊 Shooting Efficiency by Zone")
                for zone, efficiency in shot_types.items():
                    st.markdown(f"**{zone}**")
                    st.progress(efficiency/100)
                    st.write(f"Efficiency: {efficiency:.1f}%")
    
    with analysis_tabs[3]:
        st.subheader("Performance Consistency Tracker")
        selected_player = st.selectbox("Select Player:", list(all_players.keys()), key="consistency")
        
        if selected_player:
            player_data = all_players[selected_player]
            games = player_data["games"]
            
            # Game-by-game performance
            st.markdown("### 📈 Last 10 Games Performance")
            game_df = pd.DataFrame({
                "Game": range(1, len(games) + 1),
                "Points": games
            })
            st.line_chart(game_df.set_index("Game"))
            
            # Performance consistency metrics
            consistency_cols = st.columns(3)
            
            with consistency_cols[0]:
                avg_points = np.mean(games)
                st.metric("Average Points", f"{avg_points:.1f}", "Per Game")
            
            with consistency_cols[1]:
                point_range = max(games) - min(games)
                st.metric("Scoring Range", f"{point_range}", "Points")
            
            with consistency_cols[2]:
                consistency = 100 - (np.std(games) / np.mean(games) * 100)
                st.metric("Consistency Rating", f"{consistency:.1f}%", "Performance Stability")
            
            # Performance insights
            st.markdown("### 🔍 Performance Insights")
            insights = []
            
            if np.std(games) < 5:
                insights.append("👍 Highly consistent scorer")
            else:
                insights.append("⚠️ Shows scoring variability")
                
            if np.mean(games[-3:]) > np.mean(games):
                insights.append("📈 Trending upward in recent games")
            elif np.mean(games[-3:]) < np.mean(games):
                insights.append("📉 Showing slight decline in recent games")
            
            for insight in insights:
                st.write(insight)
            
            # Recommendations based on performance
            st.markdown("### 💡 Performance Enhancement Suggestions")
            if consistency < 70:
                st.info("Focus on maintaining consistent scoring output across games")
            if np.mean(games[-3:]) < np.mean(games):
                st.warning("Consider load management and recovery strategies")
            if max(games) - min(games) > 15:
                st.info("Work on minimizing performance fluctuations")

    with analysis_tabs[4]:
        st.subheader("🏆 Elite Player Insights & Game Strategy")
        
        # Top Performers Section
        st.markdown("### 🌟 Top Performers Analysis")
        
        # Calculate overall ratings for each player
        player_ratings = {}
        for player, stats in all_players.items():
            # Calculate comprehensive rating based on multiple factors
            scoring_impact = stats["PPG"] * 0.3
            efficiency = ((stats["FG%"] + stats["3P%"] + stats["FT%"]) / 3) * 0.2
            versatility = (stats["RPG"] + stats["APG"]) * 0.25
            consistency = (100 - (np.std(stats["games"]) / np.mean(stats["games"]) * 100)) * 0.25
            
            overall_rating = scoring_impact + efficiency + versatility + consistency
            player_ratings[player] = overall_rating
        
        # Sort players by rating
        top_players = dict(sorted(player_ratings.items(), key=lambda x: x[1], reverse=True))
        
        # Display top players with their strengths
        cols = st.columns(len(all_players))
        for idx, (player, rating) in enumerate(top_players.items()):
            with cols[idx]:
                st.markdown(f"""
                <div style='padding: 15px; border-radius: 10px; border: 2px solid #FF4B4B; background-color: white; text-align: center;'>
                    <h4 style='color: #FF4B4B;'>{player}</h4>
                    <p style='font-size: 24px; font-weight: bold;'>{rating:.1f}</p>
                    <p>Performance Rating</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Game Strategy Recommendations
        st.markdown("### 🎯 Strategic Recommendations")
        
        # Player selection for specific recommendations
        selected_player = st.selectbox("Select Player for Strategy:", list(all_players.keys()), key="strategy")
        
        if selected_player:
            player_data = all_players[selected_player]
            
            # Offensive Strategy Recommendations
            st.markdown("#### 🏃‍♂️ Offensive Strategies")
            offense_cols = st.columns(2)
            
            with offense_cols[0]:
                st.markdown("**Primary Options**")
                
                # Generate offensive recommendations based on player strengths
                if player_data["3P%"] >= 40:
                    st.success("💫 Prioritize 3-point opportunities through screens and pick-and-pop actions")
                if player_data["FG%"] >= 55:
                    st.success("🎯 Exploit high-percentage shots in the paint")
                if player_data["APG"] >= 7:
                    st.success("👥 Run offense through player's playmaking abilities")
                
            with offense_cols[1]:
                st.markdown("**Situational Plays**")
                
                # Late game scenarios
                if player_data["FT%"] >= 80:
                    st.info("⚡ Primary option for late-game free throw situations")
                if np.mean(player_data["games"][-3:]) > np.mean(player_data["games"]):
                    st.info("🔥 Player is in hot streak - increase usage in crucial moments")
        
            # Matchup Exploitation
            st.markdown("#### 💪 Matchup Advantages")
            
            # Calculate player's primary strength
            strengths = {
                "Perimeter Scoring": player_data["3P%"],
                "Interior Presence": player_data["FG%"],
                "Playmaking": player_data["APG"],
                "Physical Impact": player_data["RPG"]
            }
            
            primary_strength = max(strengths.items(), key=lambda x: x[1])
            
            matchup_cols = st.columns(2)
            with matchup_cols[0]:
                st.markdown("**Offensive Matchup**")
                st.info(f"Primary Advantage: {primary_strength[0]}")
                
                # Specific matchup recommendations
                if primary_strength[0] == "Perimeter Scoring":
                    st.write("• Look for mismatches against slower defenders")
                    st.write("• Utilize off-ball screens for catch-and-shoot opportunities")
                elif primary_strength[0] == "Interior Presence":
                    st.write("• Post-up against smaller defenders")
                    st.write("• Quick moves to exploit lack of rim protection")
                elif primary_strength[0] == "Playmaking":
                    st.write("• Force defensive rotations through pick-and-roll")
                    st.write("• Create mismatches for teammates")
            
            with matchup_cols[1]:
                st.markdown("**Defensive Assignment**")
                if player_data["RPG"] > 8:
                    st.write("• Strong help-side defender - utilize in zone coverage")
                if player_data["FG%"] > 50:
                    st.write("• Good positioning - key for defensive transitions")
        
            # Load Management & Rotation
            st.markdown("#### ⚡ Load Management & Rotation")
            
            # Analyze recent game trends
            recent_games = player_data["games"][-3:]
            avg_minutes = 32  # Sample data
            
            rotation_cols = st.columns(3)
            with rotation_cols[0]:
                st.metric("Optimal Minutes", f"{avg_minutes}", "Per Game")
            with rotation_cols[1]:
                st.metric("Peak Performance", "Q2 & Q4", "Quarters")
            with rotation_cols[2]:
                rest_recommendation = "Medium" if np.mean(recent_games) < np.mean(player_data["games"]) else "Low"
                st.metric("Rest Priority", rest_recommendation, "Current Status")
        
            # Real-time Adjustments
            st.markdown("#### 🔄 In-Game Adjustments")
            
            # Create dynamic recommendations based on performance patterns
            adjustments = []
            
            if np.std(recent_games) > 5:
                adjustments.append("• Monitor early game involvement to establish rhythm")
            if player_data["FG%"] > 50:
                adjustments.append("• Increase touches during momentum swings")
            if player_data["APG"] > 6:
                adjustments.append("• Initiate offense through player when second unit is struggling")
            
            for adjustment in adjustments:
                st.write(adjustment)
            
            # Performance Optimization Tips
            st.markdown("#### 💡 Performance Optimization")
            
            tips_cols = st.columns(2)
            with tips_cols[0]:
                st.markdown("**Pre-game Focus**")
                routine = [
                    f"• {'Extended' if player_data['3P%'] > 38 else 'Standard'} shooting warmup",
                    f"• {'Dynamic' if player_data['RPG'] > 8 else 'Light'} stretching routine",
                    "• Mental preparation and visualization"
                ]
                for tip in routine:
                    st.write(tip)
            
            with tips_cols[1]:
                st.markdown("**Recovery Protocol**")
                recovery = [
                    f"• {'High' if np.mean(recent_games) > 30 else 'Moderate'} intensity recovery",
                    "• Personalized cool-down routine",
                    "• Post-game assessment"
                ]
                for rec in recovery:
                    st.write(rec)
        
        # Team Strategy Overview
        st.markdown("### 📋 Team Strategy Integration")
        
        # Display team-oriented recommendations
        team_cols = st.columns(3)
        
        with team_cols[0]:
            st.markdown("**Offensive Sets**")
            best_scorer = max(all_players.items(), key=lambda x: x[1]["PPG"])
            st.write(f"• Primary scorer: {best_scorer[0]}")
            st.write("• Implement motion offense")
            st.write("• Utilize pick-and-roll combinations")
        
        with team_cols[1]:
            st.markdown("**Defensive Schemes**")
            best_defender = max(all_players.items(), key=lambda x: x[1]["RPG"])
            st.write(f"• Anchor: {best_defender[0]}")
            st.write("• Mix man-to-man and zone")
            st.write("• Strong help defense rotation")
        
        with team_cols[2]:
            st.markdown("**Rotation Strategy**")
            st.write("• Stagger star players")
            st.write("• Maintain scoring balance")
            st.write("• Situational substitutions")

with tab3:
    st.markdown("### About BUZZER AI Assistant")
    st.write("""
    BUZZER AI is an AI-powered analytics assistant designed to help coaches, players, analysts, and basketball enthusiasts leverage data for better understanding of the game.
    
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
    BUZZER AI leverages cutting-edge AI and data analysis technology:
    
    - **Generative AI**: Powered by Google's Gemini model for natural language understanding and generation
    - **Data Visualization**: Interactive charts and graphs using Matplotlib and Streamlit
    - **Statistical Analysis**: Advanced basketball metrics computation
    - **User Interface**: Responsive and intuitive design via Streamlit
    """)
    
    # Contact information
    st.markdown("### Contact & Support")
    st.write("""
    For questions, feedback, or feature requests, please contact our team:
    
    - Email: support@BUZZER AI.ai
    - Twitter: @BUZZER AI_AI
    - GitHub: github.com/basketball-iq/app
    
    Version 1.0.0 | Last Updated: March 2025
    """)
    
    # Disclaimer
    st.markdown("### Disclaimer")
    st.write("""
    BUZZER AI is currently in beta. The analysis and insights provided should be used as a supplement to, not a replacement for, professional coaching and scouting. Statistical models and AI predictions have limitations and should be interpreted with appropriate context.
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>🏀 <b>BUZZER AI</b> | Powered by Gemini AI</div>
        <div>Made with ❤️ for basketball analytics enthusiasts</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# Add feedback mechanism
with st.expander("📝 Provide Feedback"):
    feedback_text = st.text_area("Share your thoughts on BUZZER AI:", placeholder="What did you like? What could be improved?")
    feedback_rating = st.slider("Rate your experience:", 1, 5, 5)
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! We'll use it to improve BUZZER AI.")
        # In a real application, you would store this feedback in a database
