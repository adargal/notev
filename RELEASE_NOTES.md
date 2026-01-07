# Release Notes

## v1.0.0 - Initial Release

### What's New

Notev is an AI-powered assistant designed to support Operations Centers in real-time decision-making. This initial release includes:

**Core Features**
- **Event Workspaces**: Create separate workspaces for different operational cases
- **Document Upload**: Support for PDF, Word (.docx), PowerPoint (.pptx), and text files
- **AI-Powered Chat**: Ask questions and get context-aware answers based on your documents
- **Global Documents**: Share documents across all workspaces (procedures, resources, org structure)
- **Conversation History**: Full chat history preserved per workspace

**Technical Highlights**
- Powered by Claude AI (Anthropic)
- Free local embeddings with multilingual support (Hebrew + English)
- Hybrid search combining keyword (BM25) and semantic search
- Local data storage - your documents stay on your machine
- In-app API key configuration

### Downloads

| Platform | Download | Requirements |
|----------|----------|--------------|
| Windows  | `Notev-Windows.zip` | Windows 10+ (64-bit) |

### Getting Started

1. Download and extract `Notev-Windows.zip`
2. Run `Notev.exe`
3. Enter your Anthropic API key in Settings
4. Create an Event and upload documents
5. Start asking questions!

### API Keys Required

- **Anthropic API Key** (required): Get one at https://console.anthropic.com/

### Known Limitations

- Windows only (Mac/Linux coming soon)
- Single user (no authentication)
- Images in documents are not processed
- Vector store reloads on each restart

### Feedback

Report issues at: https://github.com/adargal/notev/issues
