# Notev Quick Start Guide

## Get Started in 5 Minutes

### 1. Setup (First Time Only)

```bash
# Navigate to project directory
cd /home/adar/dev/notev

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use any text editor
```

In the `.env` file, replace `your_api_key_here` with your actual Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-...your-actual-key...
```

### 2. Run the Application

```bash
# Make sure virtual environment is activated
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### 3. Access the Web Interface

Open your web browser and go to:
```
http://localhost:5000
```

### 4. First Steps

1. **Create a workspace**:
   - Click "+ New Workspace"
   - Name it (e.g., "Emergency Response - Building Fire")
   - Add a description (optional)
   - Click "Create"

2. **Upload documents**:
   - Upload global documents (procedures, resources) using "+ Upload Global Doc"
   - Upload case-specific documents using "+ Upload to Workspace"
   - Supported formats: .txt, .docx, .pptx

3. **Start chatting**:
   - Type your question in the input box
   - Examples:
     - "What are the evacuation procedures?"
     - "What resources are available for this situation?"
     - "What should be the next step?"
   - Press Enter or click "Send"

### 5. Stop the Application

Press `Ctrl+C` in the terminal where the app is running.

## Troubleshooting

**Can't access http://localhost:5000**
- Make sure the app is running (check terminal)
- Try http://127.0.0.1:5000 instead

**"ANTHROPIC_API_KEY not found"**
- Make sure you created the `.env` file
- Make sure you added your actual API key
- Restart the application after editing `.env`

**"Module not found" error**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API endpoints for integration possibilities
- Check the architecture section to understand how it works

## Daily Usage

After initial setup, you only need:

```bash
cd /home/adar/dev/notev
source venv/bin/activate  # Activate virtual environment
python app.py              # Start the application
```

Then open http://localhost:5000 in your browser.
