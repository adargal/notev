# Notev - AI-Powered Operations Center Assistant

Notev is an AI-powered assistant designed to support Operations Centers in real-time decision-making. It ingests relevant information about specific situations and synthesizes it into clear, actionable guidance, helping operators assess scenarios, consider options, and respond effectively.

## Quick Start (Windows)

**No Python required!** Download the standalone Windows executable:

1. Go to [Releases](https://github.com/adargal/notev/releases)
2. Download `Notev-Windows.zip` from the latest release
3. Extract the zip file
4. Run `Notev.exe`
5. Your browser will open automatically
6. Enter your API keys in Settings when prompted

See [DISTRIBUTION_README.txt](DISTRIBUTION_README.txt) for detailed instructions.

## Features

### Phase 1 - Assisted Decision Support

- **Multiple Workspaces**: Create separate workspaces for different operational cases
- **Document Management**:
  - Global documents (organizational procedures, resources, structure)
  - Workspace-specific documents (case-specific information)
  - Support for .txt, .docx, and .pptx files
- **Conversational Interface**: Multi-turn, context-aware chat within workspaces
- **RAG (Retrieval-Augmented Generation)**: Responses grounded in uploaded documents
- **Conflict Detection**: Identifies contradictions in documents
- **File-Based Persistence**: All data stored locally

## Technology Stack

- **Backend**: Flask (Python)
- **AI/ML**: Claude API (Anthropic)
- **Document Processing**: python-docx, python-pptx
- **Vector Search**: In-memory vector store with semantic search
- **Frontend**: HTML, CSS, JavaScript
- **Storage**: File-based (JSON + documents)

## Installation

### Prerequisites

- Python 3.11 (recommended) - Python 3.14 has compatibility issues with some dependencies
- Anthropic API key (get one at https://console.anthropic.com/)
- Voyage AI API key (get one at https://www.voyageai.com/) - **Optional but recommended for better search quality**

### Setup Steps

1. **Clone or download the project**:
   ```bash
   cd /home/adar/dev/notev
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   VOYAGE_API_KEY=your_voyage_api_key_here
   ```

   **Note on Voyage AI**: The Voyage API key is optional. Without it, the system will fall back to simple hash-based embeddings which provide basic keyword matching but not true semantic search. For production use with multiple documents, the Voyage AI embeddings are highly recommended for better search quality.

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Access the web interface**:
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Creating a Workspace

1. Click "New Workspace" in the sidebar
2. Enter a name and optional description
3. Click "Create"

### Adding Documents

**Global Documents** (available to all workspaces):
- Click "Upload Global Doc"
- Select a .txt, .docx, or .pptx file
- The document will be processed and available to all workspaces

**Workspace Documents** (specific to one case):
- Select a workspace
- Click "Upload to Workspace"
- Select a file
- The document will only be available in that workspace

### Chatting with Notev

1. Select a workspace
2. Type your question in the input box
3. Press Enter or click "Send"
4. Notev will retrieve relevant information from documents and provide guidance

### Best Practices

- **Upload relevant documents first** before asking questions
- **Use clear, specific questions** about operational scenarios
- **Global documents**: Use for procedures, resources, organizational structure
- **Workspace documents**: Use for case-specific information, incident details
- **Review responses carefully**: Notev is advisory only; operators make final decisions

## Architecture

```
notev/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create from .env.example)
│
├── notev_backend/
│   └── modules/
│       ├── document_processor.py  # Document parsing and chunking
│       ├── vector_store.py        # In-memory vector search
│       ├── workspace_manager.py   # Workspace CRUD and persistence
│       ├── global_docs_manager.py # Global documents management
│       └── chat_agent.py          # Claude integration and RAG
│
├── notev_frontend/
│   ├── templates/
│   │   └── index.html            # Main web interface
│   └── static/
│       ├── css/
│       │   └── style.css         # Styles
│       └── js/
│           └── app.js            # Frontend logic
│
└── storage/                       # Data storage (created automatically)
    ├── global_docs/              # Global documents
    └── workspaces/               # Workspace data
        └── {workspace_id}/
            ├── metadata.json     # Workspace metadata
            └── documents/        # Workspace documents
```

## API Endpoints

### Workspaces
- `GET /api/workspaces` - List all workspaces
- `POST /api/workspaces` - Create workspace
- `GET /api/workspaces/{id}` - Get workspace details
- `PUT /api/workspaces/{id}` - Update workspace
- `DELETE /api/workspaces/{id}` - Delete workspace

### Documents
- `GET /api/global-documents` - List global documents
- `POST /api/global-documents` - Upload global document
- `DELETE /api/global-documents/{id}` - Delete global document
- `GET /api/workspaces/{id}/documents` - List workspace documents
- `POST /api/workspaces/{id}/documents` - Upload workspace document
- `DELETE /api/workspaces/{id}/documents/{doc_id}` - Delete workspace document

### Chat
- `POST /api/workspaces/{id}/chat` - Send message
- `GET /api/workspaces/{id}/conversation` - Get conversation history
- `DELETE /api/workspaces/{id}/conversation` - Clear conversation

### System
- `GET /api/system/status` - Get system status

## Security Considerations

⚠️ **Important**: This is a Phase 1 implementation focused on functionality. For production use:

1. **Authentication**: Add user authentication and authorization
2. **API Key Security**: Use encrypted storage or secrets management
3. **File Upload Validation**: Implement additional file validation and scanning
4. **Rate Limiting**: Add rate limiting to API endpoints
5. **HTTPS**: Use HTTPS in production
6. **Input Sanitization**: Validate and sanitize all user inputs
7. **File Permissions**: Ensure proper file permissions on storage directories

## Known Limitations

1. **Embeddings**: Without a Voyage AI API key, uses simple hash-based embeddings (keyword matching). For best results with multiple documents, add a Voyage AI API key to your `.env` file.
2. **Single User**: No multi-user support or authentication
3. **No Pagination**: Large document sets may cause performance issues
4. **Local Only**: No cloud storage or deployment
5. **Text Only**: Images and diagrams in documents are not processed
6. **In-Memory Vector Store**: Vector embeddings are stored in memory and reloaded on each restart

## Future Enhancements (Beyond Phase 1)

- User authentication and role-based access control
- Multi-user collaboration
- Advanced conflict resolution
- Export capabilities (reports, summaries)
- Real-time notifications
- Cloud deployment options
- Mac/Linux executable packaging

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
- Ensure you've created a `.env` file from `.env.example`
- Add your actual API key to the `.env` file

**"Module not found" errors**
- Ensure you've activated the virtual environment
- Run `pip install -r requirements.txt`

**Documents not being retrieved correctly** or **Large documents interfering with search**
- Check that documents have been uploaded successfully
- Verify the document format is supported (.txt, .docx, .pptx, .pdf)
- **Recommended**: Add a Voyage AI API key to `.env` for semantic search instead of keyword matching
- Without Voyage AI, the system uses simple hash-based embeddings which may not work well with multiple or large documents
- Try uploading smaller documents first to test

**Port already in use**
- Change the port in `app.py` (default is 5000)
- Or stop the process using port 5000

## License

This project is for internal use. All rights reserved.

## Support

For issues or questions, please contact the development team.
