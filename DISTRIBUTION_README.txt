============================================================
  NOTEV - AI-Powered Operations Decision Support
============================================================

QUICK START
-----------
1. Double-click "Notev.exe" to start the application
2. Your browser will open automatically
3. On first run, you'll be prompted to enter your API keys
4. Enter your Anthropic API key (required) and optionally Voyage AI key
5. Start using Notev!


GETTING API KEYS
----------------
Anthropic API Key (Required):
  1. Go to https://console.anthropic.com/
  2. Sign up or log in
  3. Navigate to API Keys section
  4. Create a new API key
  5. Copy the key (starts with "sk-ant-")

Voyage AI API Key (Optional - improves document search):
  1. Go to https://www.voyageai.com/
  2. Sign up for an account
  3. Get your API key from the dashboard


FEATURES
--------
- Create Events (workspaces) to organize your work
- Upload documents (PDF, Word, PowerPoint, Text)
- Ask questions and get AI-powered answers based on your documents
- Conversation history is preserved per Event


SYSTEM REQUIREMENTS
-------------------
- Windows 10 or later (64-bit)
- Internet connection (required for AI features)
- Modern web browser (Chrome, Firefox, Edge)


TROUBLESHOOTING
---------------
"Port already in use":
  - Close any other applications using port 5000
  - Or wait a moment - the app will find another available port

Browser doesn't open automatically:
  - Open your browser manually
  - Go to http://127.0.0.1:5000

"API keys not configured" error:
  - Click the Settings button in the top right
  - Enter your Anthropic API key

Application won't start:
  - Make sure you're running from the Notev folder
  - Try running as Administrator
  - Check Windows Defender/antivirus isn't blocking it


DATA STORAGE
------------
Your data is stored in the "storage" folder:
  - storage/config.json - Your API keys (keep this secure!)
  - storage/workspaces/ - Your events and documents
  - storage/global_docs/ - Global documents


SECURITY NOTES
--------------
- API keys are stored locally on your computer
- No data is sent to external servers except Anthropic/Voyage AI APIs
- Keep your API keys confidential
- Don't share the storage/config.json file


SUPPORT
-------
For issues or questions, contact: [Your contact info here]


============================================================
  Powered by Claude AI from Anthropic
============================================================
