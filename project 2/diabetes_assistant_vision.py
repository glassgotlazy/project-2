import streamlit as st
import openai
import os
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
import base64
from io import BytesIO
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Diabetes AI Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .estimate-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .estimate-value {
        font-size: 3rem;
        font-weight: bold;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# System prompt for educational assistant
SYSTEM_PROMPT = """You are a diabetes education and reasoning assistant with access to meal analysis data.

CRITICAL RULES:
- You EXPLAIN insulin dose estimates that are calculated by the system
- You do NOT calculate doses yourself - you explain the reasoning
- You treat all values as rough estimates with uncertainty
- You ALWAYS emphasize individual variability and professional consultation

CAPABILITIES:
- Explain how carb estimates from meal photos were derived
- Discuss factors affecting insulin needs (carb ratio, correction factor, activity, stress)
- Educate about food composition and glycemic impact
- Provide context about absorption rates and timing

WHEN GIVEN MEAL ANALYSIS DATA:
1. Acknowledge the estimated carbs from the photo analysis
2. Explain the estimate calculation (carbs ÷ ICR + correction)
3. Discuss uncertainty factors (portion size, preparation, individual response)
4. Mention what could make actual needs higher or lower
5. Always include a calm safety disclaimer

TONE:
- Supportive, educational, non-judgmental
- Clear without being alarmist
- Emphasize learning over prescribing

OUTPUT STRUCTURE:
1. "Based on the meal analysis showing [X]g carbs..."
2. "The estimate of [Y] units uses [explain reasoning]..."
3. "Keep in mind this could vary because..."
4. "This is educational information - consult your healthcare team"

Never give definitive medical advice or specific dosing instructions."""

# Function to encode image for API
def encode_image(image):
    """Convert PIL Image to base64 string"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Function to analyze meal from image
def analyze_meal_image(image, api_key, user_settings):
    """Use GPT-4 Vision to analyze meal and estimate carbs"""
    try:
        client = openai.OpenAI(api_key=api_key)

        # Encode image
        base64_image = encode_image(image)

        # Create analysis prompt
        analysis_prompt = f"""Analyze this meal image and provide:

1. **Food Items**: List all visible foods
2. **Portion Estimates**: Estimate serving sizes
3. **Carbohydrate Content**: Estimate total carbs in grams (be specific)
4. **Macronutrients**: Estimate protein and fat content
5. **Glycemic Impact**: Note if high/medium/low glycemic index foods

User Context:
- Insulin-to-Carb Ratio (ICR): 1:{user_settings.get('icr', 10)}
- Correction Factor: 1:{user_settings.get('cf', 50)} mg/dL
- Target Blood Sugar: {user_settings.get('target_bs', 100)} mg/dL
- Current Blood Sugar: {user_settings.get('current_bs', 'Not provided')} mg/dL

Provide estimates in this format:
CARBS: [number]g
PROTEIN: [number]g  
FAT: [number]g
CONFIDENCE: [High/Medium/Low]
FOODS: [list]
NOTES: [relevant observations]"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error analyzing image: {str(e)}"

# Function to calculate insulin estimate
def calculate_insulin_estimate(carbs, current_bs, target_bs, icr, cf):
    """Calculate rough insulin estimate for educational purposes"""

    # Meal bolus (carbs ÷ ICR)
    meal_bolus = carbs / icr

    # Correction bolus (if current BS provided and above target)
    correction_bolus = 0
    if current_bs and current_bs > target_bs:
        correction_bolus = (current_bs - target_bs) / cf

    total_estimate = meal_bolus + correction_bolus

    return {
        'total': round(total_estimate, 1),
        'meal_bolus': round(meal_bolus, 1),
        'correction_bolus': round(correction_bolus, 1),
        'carbs': carbs,
        'icr': icr,
        'cf': cf
    }

# Function to get API key
def get_api_key():
    """Get API key from Streamlit secrets, environment variable, or user input"""
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        return env_key

    if 'api_key' in st.session_state and st.session_state.api_key:
        return st.session_state.api_key

    return None

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

if 'conversation_count' not in st.session_state:
    st.session_state.conversation_count = 0

if 'glucose_log' not in st.session_state:
    st.session_state.glucose_log = []

if 'meal_log' not in st.session_state:
    st.session_state.meal_log = []

if 'learning_mode' not in st.session_state:
    st.session_state.learning_mode = False

if 'model' not in st.session_state:
    st.session_state.model = "gpt-4o"

if 'show_insights' not in st.session_state:
    st.session_state.show_insights = True

if 'user_settings' not in st.session_state:
    st.session_state.user_settings = {
        'icr': 10,
        'cf': 50,
        'target_bs': 100,
        'current_bs': None
    }

if 'last_meal_analysis' not in st.session_state:
    st.session_state.last_meal_analysis = None

if 'last_estimate' not in st.session_state:
    st.session_state.last_estimate = None

# Get API key
API_KEY = get_api_key()

# Header
st.markdown("""
<div class="main-header">
    <h1>🩺 AI Diabetes Education Assistant</h1>
    <p style='font-size: 1.1em; margin: 0;'>Photo-based meal analysis with intelligent insulin insights</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key Status
    if API_KEY:
        st.success("✅ API Key: Connected")
        key_source = "🔐 Streamlit Secrets" if "OPENAI_API_KEY" in st.secrets else "🌍 Environment Variable"
        st.caption(f"Source: {key_source}")
    else:
        st.warning("⚠️ API Key: Not configured")
        api_key_input = st.text_input(
            "Enter OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            help="Required for vision and chat features"
        )

        if api_key_input:
            st.session_state.api_key = api_key_input
            API_KEY = api_key_input

    st.markdown("---")

    # User Settings
    st.subheader("👤 Your Settings")

    with st.expander("📊 Insulin Parameters", expanded=True):
        st.session_state.user_settings['icr'] = st.number_input(
            "Insulin-to-Carb Ratio (1:X)",
            min_value=1,
            max_value=30,
            value=st.session_state.user_settings['icr'],
            help="How many grams of carbs covered by 1 unit"
        )

        st.session_state.user_settings['cf'] = st.number_input(
            "Correction Factor (1:X mg/dL)",
            min_value=10,
            max_value=150,
            value=st.session_state.user_settings['cf'],
            help="How much 1 unit lowers blood sugar"
        )

        st.session_state.user_settings['target_bs'] = st.number_input(
            "Target Blood Sugar (mg/dL)",
            min_value=70,
            max_value=130,
            value=st.session_state.user_settings['target_bs'],
            help="Your target glucose level"
        )

    st.markdown("---")

    # Model selection
    st.session_state.model = st.selectbox(
        "🤖 AI Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        help="GPT-4o recommended for vision"
    )

    st.markdown("---")

    # Learning mode
    st.session_state.learning_mode = st.toggle(
        "🎓 Learning Mode",
        value=st.session_state.learning_mode,
        help="Detailed educational explanations"
    )

    st.session_state.show_insights = st.toggle(
        "📊 Show Analytics",
        value=st.session_state.show_insights,
        help="Display trends and patterns"
    )

    st.markdown("---")

    # Statistics
    st.subheader("📈 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analyzed", len([m for m in st.session_state.meal_log if 'image_analysis' in m]))
    with col2:
        st.metric("Total Logs", len(st.session_state.glucose_log) + len(st.session_state.meal_log))

    st.markdown("---")

    # Quick actions
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.messages = []
        st.session_state.glucose_log = []
        st.session_state.meal_log = []
        st.session_state.conversation_count = 0
        st.session_state.last_meal_analysis = None
        st.session_state.last_estimate = None
        st.rerun()

    st.markdown("---")

    # Export data
    if st.button("📥 Export Logs (JSON)", use_container_width=True):
        export_data = {
            'glucose_log': st.session_state.glucose_log,
            'meal_log': st.session_state.meal_log,
            'settings': st.session_state.user_settings,
            'exported_at': datetime.now().isoformat()
        }
        st.download_button(
            "⬇️ Download",
            data=json.dumps(export_data, indent=2),
            file_name=f"diabetes_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# Main content
st.subheader("📸 Meal Photo Analysis")

# Photo upload section
col_upload, col_manual = st.columns([3, 2])

with col_upload:
    st.markdown("### 📷 Upload Meal Photo")
    uploaded_file = st.file_uploader(
        "Take or upload a photo of your meal",
        type=['png', 'jpg', 'jpeg'],
        help="AI will analyze the meal and estimate carbs"
    )

    # Camera input option
    camera_photo = st.camera_input("Or take a photo now")

    # Use camera photo if available
    if camera_photo:
        uploaded_file = camera_photo

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Your Meal", use_container_width=True)

        # Current blood sugar input
        current_bs_input = st.number_input(
            "Current Blood Sugar (optional, mg/dL)",
            min_value=40,
            max_value=400,
            value=None,
            help="For correction dose calculation"
        )

        if current_bs_input:
            st.session_state.user_settings['current_bs'] = current_bs_input

        # Analyze button
        if st.button("🔍 Analyze Meal & Calculate Estimate", type="primary", use_container_width=True):
            if not API_KEY:
                st.error("⚠️ Please configure your API key first!")
            else:
                with st.spinner("🤖 AI is analyzing your meal..."):
                    # Analyze image
                    analysis = analyze_meal_image(
                        image, 
                        API_KEY,
                        st.session_state.user_settings
                    )

                    st.session_state.last_meal_analysis = analysis

                    # Parse carbs from analysis
                    try:
                        carbs_line = [line for line in analysis.split('
') if 'CARBS:' in line][0]
                        carbs = float(carbs_line.split('CARBS:')[1].strip().replace('g', ''))

                        # Calculate estimate
                        estimate = calculate_insulin_estimate(
                            carbs,
                            st.session_state.user_settings.get('current_bs'),
                            st.session_state.user_settings['target_bs'],
                            st.session_state.user_settings['icr'],
                            st.session_state.user_settings['cf']
                        )

                        st.session_state.last_estimate = estimate

                        # Log the meal
                        st.session_state.meal_log.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'carbs': carbs,
                            'estimate': estimate['total'],
                            'image_analysis': analysis,
                            'settings_used': st.session_state.user_settings.copy()
                        })

                        st.success("✅ Meal analyzed successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error parsing analysis: {str(e)}")
                        st.text(analysis)

with col_manual:
    st.markdown("### ✍️ Manual Entry")

    with st.form("manual_meal_form"):
        meal_name = st.text_input("Meal Name", placeholder="e.g., Breakfast")
        manual_carbs = st.number_input("Carbs (g)", min_value=0, max_value=300, value=50, step=5)
        manual_bs = st.number_input("Current Blood Sugar (mg/dL)", min_value=40, max_value=400, value=None)

        submitted = st.form_submit_button("Calculate Estimate", use_container_width=True)

        if submitted:
            estimate = calculate_insulin_estimate(
                manual_carbs,
                manual_bs,
                st.session_state.user_settings['target_bs'],
                st.session_state.user_settings['icr'],
                st.session_state.user_settings['cf']
            )

            st.session_state.last_estimate = estimate
            st.session_state.last_meal_analysis = f"Manual entry: {meal_name}
CARBS: {manual_carbs}g"

            # Log the meal
            st.session_state.meal_log.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'meal': meal_name,
                'carbs': manual_carbs,
                'estimate': estimate['total'],
                'manual_entry': True,
                'settings_used': st.session_state.user_settings.copy()
            })

            st.success("✅ Estimate calculated!")
            st.rerun()

# Display latest estimate
if st.session_state.last_estimate:
    st.markdown("---")
    estimate = st.session_state.last_estimate

    col_est1, col_est2 = st.columns([2, 3])

    with col_est1:
        st.markdown(f"""
        <div class="estimate-card">
            <h3 style='margin:0;'>Insulin Estimate</h3>
            <div class="estimate-value">{estimate['total']} units</div>
            <p style='margin:0; opacity:0.9;'>
                Meal: {estimate['meal_bolus']}u | Correction: {estimate['correction_bolus']}u
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.info(f"""
        **Calculation Basis:**
        - {estimate['carbs']}g carbs ÷ {estimate['icr']} (ICR) = {estimate['meal_bolus']}u
        - Correction: {estimate['correction_bolus']}u

        ⚠️ **This is an educational estimate only!**
        """)

    with col_est2:
        if st.session_state.last_meal_analysis:
            with st.expander("📋 Meal Analysis Details", expanded=True):
                st.text(st.session_state.last_meal_analysis)

        # Ask AI button
        if st.button("🤖 Ask AI to Explain This Estimate", use_container_width=True):
            explanation_prompt = f"""The system calculated an insulin estimate for my meal:

**Meal Analysis:**
{st.session_state.last_meal_analysis}

**Estimate Calculation:**
- Total: {estimate['total']} units
- Meal bolus: {estimate['meal_bolus']} units (from {estimate['carbs']}g carbs ÷ ICR 1:{estimate['icr']})
- Correction: {estimate['correction_bolus']} units

Can you explain this estimate and what factors might affect my actual insulin needs?"""

            st.session_state.messages.append({"role": "user", "content": explanation_prompt})
            st.rerun()

# Chat interface
st.markdown("---")
st.subheader("💬 Chat with AI Educator")

# Chat container
chat_container = st.container(height=400)
with chat_container:
    if len(st.session_state.messages) == 0:
        st.markdown("""
        <div class="info-box">
            <h4>👋 How I can help:</h4>
            <ul>
                <li>🍽️ Explain meal analysis results and carb estimates</li>
                <li>💉 Break down insulin calculations step-by-step</li>
                <li>📚 Educate about factors affecting insulin needs</li>
                <li>🎯 Discuss timing, exercise, and stress impacts</li>
            </ul>
            <p><strong>Remember:</strong> I explain estimates, but only your healthcare team should guide actual dosing!</p>
        </div>
        """, unsafe_allow_html=True)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "timestamp" in message:
                st.caption(f"🕒 {message['timestamp']}")

# Chat input
if prompt := st.chat_input("Ask about your meal analysis or insulin estimates..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.conversation_count += 1
    st.rerun()

# Process chat
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    with chat_container:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if not API_KEY:
                message_placeholder.error("⚠️ Please configure your API key")
            else:
                try:
                    client = openai.OpenAI(api_key=API_KEY)

                    # Prepare context with meal logs
                    context = ""
                    if st.session_state.meal_log:
                        recent_meals = st.session_state.meal_log[-3:]
                        context = "

RECENT MEAL LOG:
"
                        for meal in recent_meals:
                            context += f"- {meal['timestamp']}: {meal.get('carbs', 'N/A')}g carbs, {meal.get('estimate', 'N/A')}u estimated
"

                    # Prepare messages
                    api_messages = [{"role": "system", "content": SYSTEM_PROMPT + context}]

                    if st.session_state.learning_mode:
                        api_messages.append({
                            "role": "system",
                            "content": "LEARNING MODE: Provide detailed educational explanations with examples."
                        })

                    for msg in st.session_state.messages:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})

                    # Stream response
                    full_response = ""
                    stream = client.chat.completions.create(
                        model=st.session_state.model,
                        messages=api_messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=1500
                    )

                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    st.caption(f"🕒 {timestamp}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": timestamp
                    })

                except Exception as e:
                    message_placeholder.error(f"⚠️ Error: {str(e)}")

# Analytics section
if st.session_state.show_insights and st.session_state.meal_log:
    st.markdown("---")
    st.subheader("📊 Meal & Insulin Insights")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        total_meals = len(st.session_state.meal_log)
        st.metric("Meals Analyzed", total_meals)

    with col_b:
        avg_carbs = sum(m.get('carbs', 0) for m in st.session_state.meal_log) / max(len(st.session_state.meal_log), 1)
        st.metric("Avg Carbs/Meal", f"{avg_carbs:.1f}g")

    with col_c:
        avg_insulin = sum(m.get('estimate', 0) for m in st.session_state.meal_log) / max(len(st.session_state.meal_log), 1)
        st.metric("Avg Estimate", f"{avg_insulin:.1f}u")

    # Meal history table
    if st.session_state.meal_log:
        st.markdown("### 📋 Recent Meal History")

        meal_data = []
        for meal in st.session_state.meal_log[-10:]:
            meal_data.append({
                'Time': meal['timestamp'],
                'Meal': meal.get('meal', 'Photo analysis'),
                'Carbs (g)': meal.get('carbs', 'N/A'),
                'Estimate (u)': meal.get('estimate', 'N/A'),
                'Type': '📸 Photo' if 'image_analysis' in meal else '✍️ Manual'
            })

        st.dataframe(meal_data, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
    <p style='margin: 0; color: #d9534f; font-weight: bold;'>
        ⚠️ CRITICAL MEDICAL DISCLAIMER
    </p>
    <p style='margin: 0.5rem 0; color: #666;'>
        This tool provides <strong>educational estimates only</strong>. It does NOT calculate actual insulin doses for use.
        AI meal analysis may be inaccurate. ALWAYS verify with your healthcare provider before taking any insulin.
        Never adjust your insulin based solely on this app. Individual factors affect insulin needs significantly.
    </p>
    <p style='margin-top: 0.5rem; color: #999; font-size: 0.9em;'>
        Made for diabetes education | Powered by OpenAI GPT-4 Vision
    </p>
</div>
""", unsafe_allow_html=True)
