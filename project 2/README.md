# 🩺 AI Diabetes Education Assistant with Vision

Advanced diabetes education tool with **AI-powered meal photo analysis** and intelligent insulin estimate explanations.

## ✨ Key Features

### 🤖 AI Vision Analysis
- **📸 Photo Analysis**: Upload or take photos of meals
- **GPT-4 Vision**: Automatically identifies foods and estimates carbs
- **Nutritional Breakdown**: Analyzes carbs, protein, fat, and glycemic impact
- **Confidence Levels**: Shows analysis certainty

### 💉 Educational Estimates
- **Calculation Transparency**: Shows how estimates are derived
- **ICR-Based**: Uses your insulin-to-carb ratio
- **Correction Factor**: Includes high blood sugar corrections
- **Step-by-Step**: Breaks down meal bolus + correction bolus

### 🎓 AI Educator
- **Context-Aware**: AI has access to your meal log history
- **Explains Estimates**: Breaks down the reasoning behind calculations
- **Educational Focus**: Teaches rather than prescribes
- **Safety-First**: Emphasizes professional consultation

### 📊 Comprehensive Tracking
- **Meal History**: Logs all analyzed meals with timestamps
- **Analytics Dashboard**: Trends and averages
- **Export Data**: Download logs as JSON
- **Visual Charts**: Plotly-powered visualizations

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Set up your OpenAI API key (choose one):

**Option 1: Streamlit Secrets**
```bash
mkdir -p .streamlit
echo 'OPENAI_API_KEY = "sk-your-key"' > .streamlit/secrets.toml
```

**Option 2: Environment Variable**
```bash
export OPENAI_API_KEY='sk-your-key'
```

### Run
```bash
streamlit run diabetes_assistant_vision.py
```

## 📖 How to Use

### 1. Configure Your Settings
In the sidebar, enter your:
- **ICR (Insulin-to-Carb Ratio)**: e.g., 1:10 means 1 unit covers 10g carbs
- **Correction Factor**: e.g., 1:50 means 1 unit lowers BS by 50 mg/dL
- **Target Blood Sugar**: Your goal glucose level

### 2. Analyze a Meal
**Photo Analysis:**
1. Click "Browse files" or use camera
2. Upload/take a photo of your meal
3. (Optional) Enter current blood sugar
4. Click "Analyze Meal & Calculate Estimate"
5. Review AI's carb estimate and calculation

**Manual Entry:**
- Use the form for quick manual entries
- Enter meal name, carbs, and current BS
- Get instant estimate calculation

### 3. Learn from AI
- Click "Ask AI to Explain This Estimate"
- Chat with AI about factors affecting insulin needs
- AI has access to your meal history for context
- Ask about exercise, stress, timing, etc.

### 4. Track Your Data
- View meal history table
- See analytics and averages
- Export logs for sharing with healthcare team

## 🎯 Example Use Cases

### Scenario 1: Restaurant Meal
```
1. Take photo of pasta dish
2. AI estimates: 75g carbs
3. System calculates: 7.5u (75g ÷ 10 ICR)
4. Ask AI: "Why might I need more/less for this pasta?"
5. AI explains: fat content, sauce type, timing factors
```

### Scenario 2: High Blood Sugar Correction
```
1. Manual entry: 0g carbs, BS 180 mg/dL
2. System calculates: 1.6u correction ((180-100) ÷ 50)
3. Ask AI: "Explain this correction dose"
4. AI discusses: correction factor, timing, trends
```

### Scenario 3: Complex Meal
```
1. Photo of mixed meal with rice, chicken, vegetables
2. AI analyzes: 65g carbs, 30g protein, 15g fat
3. System estimates: 6.5u
4. AI explains: protein/fat may slow absorption
5. Discusses: extended bolus considerations
```

## ⚙️ Technical Details

### Models
- **Vision**: GPT-4 Vision (gpt-4o recommended)
- **Chat**: GPT-4o / GPT-4 Turbo / GPT-3.5 Turbo
- **Streaming**: Real-time response generation

### Calculations
```python
Meal Bolus = Carbs (g) ÷ ICR
Correction Bolus = (Current BS - Target BS) ÷ Correction Factor
Total Estimate = Meal Bolus + Correction Bolus
```

### Data Storage
- Session-based (not persistent across restarts)
- Export to JSON for backup
- No database required

## 🔒 Safety Features

### Built-in Safeguards
- ✅ Estimates labeled as "educational only"
- ✅ AI instructed to explain, not prescribe
- ✅ Prominent medical disclaimers
- ✅ Encourages professional consultation
- ✅ Emphasizes individual variability

### What This App Does NOT Do
- ❌ Calculate actual insulin doses for use
- ❌ Provide medical advice
- ❌ Replace healthcare providers
- ❌ Guarantee accuracy of estimates
- ❌ Account for all individual factors

## 🛠️ Technology Stack
- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4 Vision + Chat
- **Image Processing**: PIL (Pillow)
- **Visualization**: Plotly
- **Data**: JSON export

## 📝 Important Notes

### Vision Analysis Accuracy
- AI estimates may be inaccurate
- Portion sizes are approximated
- Preparation methods affect carbs
- Hidden ingredients may be missed
- **Always verify with nutrition labels**

### Individual Variability
- ICR varies by time of day
- Exercise affects insulin sensitivity
- Stress/illness increases needs
- Menstrual cycles impact requirements
- **These factors are not accounted for**

### Medical Disclaimer
This application is for **educational purposes ONLY**. Never adjust insulin based solely on this app. Always consult your endocrinologist, diabetes educator, or healthcare provider for medical decisions.

## 🤝 Contributing
Educational tool for demonstration purposes. Feel free to fork and enhance!

## 📄 License
For educational use only.

---

**Made with ❤️ for diabetes education**
