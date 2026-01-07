"""
Notev Flask Application
Main application file with REST API endpoints for workspace and document management.
"""
from flask import Flask, request, jsonify, render_template, send_from_directory, Response, stream_with_context
from flask_cors import CORS
import json
from werkzeug.utils import secure_filename
import os
import re
import unicodedata
from pathlib import Path

from config import Config
from notev_backend.modules.document_processor import DocumentProcessor
from notev_backend.modules.vector_store import VectorStore
from notev_backend.modules.workspace_manager import WorkspaceManager
from notev_backend.modules.global_docs_manager import GlobalDocsManager
from notev_backend.modules.chat_agent import ChatAgent

# Module instances (initialized after config is loaded)
vector_store = None
chat_agent = None


def secure_filename_unicode(filename):
    """
    Secure filename that preserves Unicode characters (including Hebrew).

    This is an alternative to werkzeug's secure_filename which strips non-ASCII.
    It preserves Unicode characters while still removing dangerous path components.
    """
    # Normalize unicode
    filename = unicodedata.normalize('NFKC', filename)

    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove null bytes and other control characters
    filename = ''.join(c for c in filename if c.isprintable() or c.isspace())

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Ensure we have something left
    if not filename or filename in ('.', '..'):
        filename = 'unnamed_file'

    # Limit length (preserve extension)
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext

    return filename


# Initialize Flask app
app = Flask(__name__,
            static_folder='notev_frontend/static',
            template_folder='notev_frontend/templates')
app.config.from_object(Config)
CORS(app)

# Initialize storage first
Config.init_storage()

# Load API keys from config file or environment
Config.load_api_keys()

# Check if configured (don't exit if not - allow settings UI to configure)
if not Config.is_configured():
    print("\n" + "="*60)
    print("WARNING: API keys not configured!")
    print("Please open the app and configure your API keys in Settings.")
    print("="*60 + "\n")

# Initialize modules that don't require API keys
document_processor = DocumentProcessor(
    chunk_size=Config.CHUNK_SIZE,
    chunk_overlap=Config.CHUNK_OVERLAP
)

workspace_manager = WorkspaceManager(Config.WORKSPACES_PATH)

global_docs_manager = GlobalDocsManager(Config.GLOBAL_DOCS_PATH)


def initialize_ai_modules():
    """Initialize or reinitialize AI modules with current API keys."""
    global vector_store, chat_agent

    if not Config.ANTHROPIC_API_KEY:
        vector_store = None
        chat_agent = None
        return False

    vector_store = VectorStore(
        local_model=Config.LOCAL_EMBEDDING_MODEL,
        model_cache_dir=Config.get_model_cache_dir(),
        search_mode=Config.SEARCH_MODE
    )

    chat_agent = ChatAgent(
        api_key=Config.ANTHROPIC_API_KEY,
        model=Config.CLAUDE_MODEL,
        max_tokens=Config.MAX_TOKENS,
        temperature=Config.TEMPERATURE
    )

    return True


# Initialize AI modules if configured
initialize_ai_modules()


# ============================================================================
# Vector Store Initialization - Reload all documents
# ============================================================================

def reload_all_documents_to_vector_store():
    """
    Reload all existing documents into the vector store on app startup.
    This is necessary because the vector store is in-memory only.
    """
    global vector_store

    if vector_store is None:
        print("\n" + "="*60)
        print("SKIPPING DOCUMENT RELOAD - API keys not configured")
        print("="*60 + "\n")
        return

    print("\n" + "="*60)
    print("RELOADING DOCUMENTS INTO VECTOR STORE")
    print("="*60)

    # Reload global documents
    global_docs = global_docs_manager.list_documents()
    print(f"\nFound {len(global_docs)} global document(s) to load")
    for doc in global_docs:
        try:
            # Use the file_path from metadata (which has the correct path)
            doc_path = Path(doc['file_path'])
            print(f"  Checking: {doc['original_filename']} at {doc_path}")
            if doc_path.exists():
                print(f"    File found, processing...")
                doc_data = document_processor.process_document(str(doc_path))
                vector_doc_id = f"global_{doc['id']}"
                vector_store.add_document(
                    vector_doc_id,
                    doc_data['chunks'],
                    metadata={
                        'doc_id': doc['id'],
                        'filename': doc['original_filename'],
                        'type': 'global'
                    }
                )
                print(f"  ✓ Loaded global document: {doc['original_filename']} ({doc_data['num_chunks']} chunks)")
            else:
                print(f"    ✗ File not found at path: {doc_path}")
        except Exception as e:
            print(f"  ✗ Error loading global document {doc.get('original_filename', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()

    # Reload workspace documents
    workspaces = workspace_manager.list_workspaces()
    print(f"\nFound {len(workspaces)} workspace(s) to check")
    for workspace in workspaces:
        workspace_id = workspace['id']
        workspace_docs = workspace_manager.get_workspace_documents(workspace_id)
        print(f"  Workspace '{workspace['name']}': {len(workspace_docs)} document(s)")

        for doc in workspace_docs:
            try:
                doc_path = Config.WORKSPACES_PATH / workspace_id / 'documents' / doc['id'] / doc['original_filename']
                if doc_path.exists():
                    doc_data = document_processor.process_document(str(doc_path))
                    vector_doc_id = f"workspace_{workspace_id}_{doc['id']}"
                    vector_store.add_document(
                        vector_doc_id,
                        doc_data['chunks'],
                        metadata={
                            'workspace_id': workspace_id,
                            'doc_id': doc['id'],
                            'filename': doc['original_filename'],
                            'type': 'workspace'
                        }
                    )
                    print(f"  ✓ Loaded workspace document: {doc['original_filename']} (Event: {workspace['name']})")
            except Exception as e:
                print(f"  ✗ Error loading workspace document {doc['original_filename']}: {e}")

    stats = vector_store.get_stats()
    print(f"\n" + "="*60)
    print(f"VECTOR STORE LOADED:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total documents: {stats['total_documents']}")
    print("="*60 + "\n")

# Reload all documents on startup
reload_all_documents_to_vector_store()


# ============================================================================
# Web UI Routes
# ============================================================================

@app.route('/')
def index():
    """Serve main web interface."""
    return render_template('index.html')


# ============================================================================
# Workspace Management API
# ============================================================================

@app.route('/api/workspaces', methods=['GET'])
def list_workspaces():
    """List all workspaces."""
    workspaces = workspace_manager.list_workspaces()
    return jsonify({'workspaces': workspaces})


@app.route('/api/workspaces', methods=['POST'])
def create_workspace():
    """Create a new workspace."""
    data = request.json

    if not data or 'name' not in data:
        return jsonify({'error': 'Workspace name is required'}), 400

    workspace = workspace_manager.create_workspace(
        name=data['name'],
        description=data.get('description', '')
    )

    return jsonify({'workspace': workspace}), 201


@app.route('/api/workspaces/<workspace_id>', methods=['GET'])
def get_workspace(workspace_id):
    """Get workspace details."""
    workspace = workspace_manager.get_workspace(workspace_id)

    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404

    return jsonify({'workspace': workspace})


@app.route('/api/workspaces/<workspace_id>', methods=['PUT'])
def update_workspace(workspace_id):
    """Update workspace metadata."""
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    success = workspace_manager.update_workspace(
        workspace_id,
        name=data.get('name'),
        description=data.get('description')
    )

    if not success:
        return jsonify({'error': 'Workspace not found'}), 404

    workspace = workspace_manager.get_workspace(workspace_id)
    return jsonify({'workspace': workspace})


@app.route('/api/workspaces/<workspace_id>', methods=['DELETE'])
def delete_workspace(workspace_id):
    """Delete a workspace."""
    success = workspace_manager.delete_workspace(workspace_id)

    if not success:
        return jsonify({'error': 'Workspace not found'}), 404

    return jsonify({'message': 'Workspace deleted successfully'})


# ============================================================================
# Workspace Documents API
# ============================================================================

@app.route('/api/workspaces/<workspace_id>/documents', methods=['GET'])
def get_workspace_documents(workspace_id):
    """Get all documents in a workspace."""
    documents = workspace_manager.get_workspace_documents(workspace_id)
    return jsonify({'documents': documents})


@app.route('/api/workspaces/<workspace_id>/documents', methods=['POST'])
def add_workspace_document(workspace_id):
    """Add a document to a workspace."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save uploaded file temporarily
    filename = secure_filename_unicode(file.filename)
    temp_path = Config.STORAGE_PATH / 'temp' / filename
    temp_path.parent.mkdir(exist_ok=True)

    try:
        file.save(temp_path)

        # Validate file
        is_valid, error_msg = document_processor.validate_file(str(temp_path))
        if not is_valid:
            temp_path.unlink()
            return jsonify({'error': error_msg}), 400

        # Process document
        doc_data = document_processor.process_document(str(temp_path))

        # Add to workspace
        doc_id = workspace_manager.add_document_to_workspace(
            workspace_id,
            str(temp_path),
            {
                'filename': filename,
                'file_type': doc_data['file_type'],
                'num_chunks': doc_data['num_chunks'],
                'total_chars': doc_data['total_chars']
            }
        )

        if not doc_id:
            temp_path.unlink()
            return jsonify({'error': 'Failed to add document to workspace'}), 500

        # Add to vector store with workspace-specific ID
        vector_doc_id = f"workspace_{workspace_id}_{doc_id}"
        vector_store.add_document(
            vector_doc_id,
            doc_data['chunks'],
            metadata={
                'workspace_id': workspace_id,
                'doc_id': doc_id,
                'filename': filename,
                'type': 'workspace'
            }
        )

        return jsonify({
            'message': 'Document added successfully',
            'doc_id': doc_id,
            'filename': filename,
            'num_chunks': doc_data['num_chunks']
        }), 201

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'error': str(e)}), 500


@app.route('/api/workspaces/<workspace_id>/documents/<doc_id>/content', methods=['GET'])
def get_workspace_document_content(workspace_id, doc_id):
    """Get content of a workspace document."""
    docs = workspace_manager.get_workspace_documents(workspace_id)
    doc = next((d for d in docs if d['id'] == doc_id), None)

    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    try:
        file_path = doc['file_path']
        processed_doc = document_processor.process_document(file_path)

        return jsonify({
            'full_text': processed_doc['full_text'],
            'file_type': processed_doc['file_type'],
            'num_chunks': processed_doc['num_chunks'],
            'total_chars': processed_doc['total_chars']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workspaces/<workspace_id>/documents/<doc_id>', methods=['DELETE'])
def remove_workspace_document(workspace_id, doc_id):
    """Remove a document from a workspace."""
    # Remove from vector store
    vector_doc_id = f"workspace_{workspace_id}_{doc_id}"
    vector_store.remove_document(vector_doc_id)

    # Remove from workspace
    success = workspace_manager.remove_document_from_workspace(workspace_id, doc_id)

    if not success:
        return jsonify({'error': 'Document not found'}), 404

    return jsonify({'message': 'Document removed successfully'})


# ============================================================================
# Global Documents API
# ============================================================================

@app.route('/api/global-documents', methods=['GET'])
def list_global_documents():
    """List all global documents."""
    documents = global_docs_manager.list_documents()
    return jsonify({'documents': documents})


@app.route('/api/global-documents', methods=['POST'])
def add_global_document():
    """Add a global document."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename_unicode(file.filename)
    temp_path = Config.STORAGE_PATH / 'temp' / filename
    temp_path.parent.mkdir(exist_ok=True)

    try:
        file.save(temp_path)

        # Validate and process document
        is_valid, error_msg = document_processor.validate_file(str(temp_path))
        if not is_valid:
            temp_path.unlink()
            return jsonify({'error': error_msg}), 400

        doc_data = document_processor.process_document(str(temp_path))

        # Add to global docs
        doc_id = global_docs_manager.add_document(
            str(temp_path),
            {
                'filename': filename,
                'file_type': doc_data['file_type'],
                'num_chunks': doc_data['num_chunks'],
                'total_chars': doc_data['total_chars']
            }
        )

        if not doc_id:
            temp_path.unlink()
            return jsonify({'error': 'Failed to add global document'}), 500

        # Add to vector store with global ID
        vector_doc_id = f"global_{doc_id}"
        vector_store.add_document(
            vector_doc_id,
            doc_data['chunks'],
            metadata={
                'doc_id': doc_id,
                'filename': filename,
                'type': 'global'
            }
        )

        return jsonify({
            'message': 'Global document added successfully',
            'doc_id': doc_id,
            'filename': filename,
            'num_chunks': doc_data['num_chunks']
        }), 201

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'error': str(e)}), 500


@app.route('/api/global-documents/<doc_id>/content', methods=['GET'])
def get_global_document_content(doc_id):
    """Get content of a global document."""
    doc = global_docs_manager.get_document(doc_id)

    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    try:
        file_path = doc['file_path']
        processed_doc = document_processor.process_document(file_path)

        return jsonify({
            'full_text': processed_doc['full_text'],
            'file_type': processed_doc['file_type'],
            'num_chunks': processed_doc['num_chunks'],
            'total_chars': processed_doc['total_chars']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/global-documents/<doc_id>', methods=['DELETE'])
def remove_global_document(doc_id):
    """Remove a global document."""
    # Remove from vector store
    vector_doc_id = f"global_{doc_id}"
    vector_store.remove_document(vector_doc_id)

    # Remove from global docs
    success = global_docs_manager.remove_document(doc_id)

    if not success:
        return jsonify({'error': 'Document not found'}), 404

    return jsonify({'message': 'Global document removed successfully'})


# ============================================================================
# Chat API
# ============================================================================

@app.route('/api/workspaces/<workspace_id>/chat', methods=['POST'])
def chat(workspace_id):
    """Send a chat message and get response."""
    # Check if AI modules are configured
    if not Config.is_configured() or vector_store is None or chat_agent is None:
        return jsonify({
            'error': 'API keys not configured. Please configure your API keys in Settings.'
        }), 503

    data = request.json

    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400

    message = data['message']
    top_k = data.get('top_k', 5)

    # Get workspace to ensure it exists
    workspace = workspace_manager.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404

    # Get workspace documents IDs for filtering
    workspace_docs = workspace_manager.get_workspace_documents(workspace_id)
    workspace_doc_ids = [f"workspace_{workspace_id}_{doc['id']}" for doc in workspace_docs]

    # Get global documents IDs
    global_docs = global_docs_manager.list_documents()
    global_doc_ids = [f"global_{doc['id']}" for doc in global_docs]

    # Combine for search
    all_doc_ids = workspace_doc_ids + global_doc_ids

    # Retrieve relevant documents
    retrieved_docs = vector_store.search(message, top_k=top_k, filter_doc_ids=all_doc_ids)

    # Get conversation history
    conversation_history = workspace_manager.get_conversation_history(workspace_id, limit=10)

    # Generate response
    response_data = chat_agent.generate_response(message, conversation_history, retrieved_docs)

    # Save conversation turn
    workspace_manager.add_conversation_turn(
        workspace_id,
        'user',
        message,
        metadata={'retrieved_docs_count': len(retrieved_docs)}
    )

    workspace_manager.add_conversation_turn(
        workspace_id,
        'assistant',
        response_data['response'],
        metadata=response_data.get('usage', {})
    )

    return jsonify({
        'response': response_data['response'],
        'retrieved_docs': retrieved_docs,
        'metadata': {
            'model': response_data.get('model'),
            'usage': response_data.get('usage'),
            'retrieved_docs_count': len(retrieved_docs)
        }
    })


@app.route('/api/workspaces/<workspace_id>/chat/stream', methods=['POST'])
def chat_stream(workspace_id):
    """Send a chat message and stream the response using Server-Sent Events."""
    # Check if AI modules are configured
    if not Config.is_configured() or vector_store is None or chat_agent is None:
        return jsonify({
            'error': 'API keys not configured. Please configure your API keys in Settings.'
        }), 503

    data = request.json

    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400

    message = data['message']
    top_k = data.get('top_k', 5)

    # Get workspace to ensure it exists
    workspace = workspace_manager.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404

    # Get workspace documents IDs for filtering
    workspace_docs = workspace_manager.get_workspace_documents(workspace_id)
    workspace_doc_ids = [f"workspace_{workspace_id}_{doc['id']}" for doc in workspace_docs]

    # Get global documents IDs
    global_docs = global_docs_manager.list_documents()
    global_doc_ids = [f"global_{doc['id']}" for doc in global_docs]

    # Combine for search
    all_doc_ids = workspace_doc_ids + global_doc_ids

    # Retrieve relevant documents (done before streaming starts)
    retrieved_docs = vector_store.search(message, top_k=top_k, filter_doc_ids=all_doc_ids)

    # Get conversation history
    conversation_history = workspace_manager.get_conversation_history(workspace_id, limit=10)

    def generate():
        """Generator function for SSE streaming."""
        full_response = ""
        try:
            for chunk in chat_agent.generate_response_stream(message, conversation_history, retrieved_docs):
                full_response += chunk
                # Yield SSE formatted data with explicit newlines for flushing
                yield f"data: {json.dumps({'text': chunk})}\n\n"

            # Save conversation turns after streaming completes
            workspace_manager.add_conversation_turn(
                workspace_id,
                'user',
                message,
                metadata={'retrieved_docs_count': len(retrieved_docs)}
            )

            workspace_manager.add_conversation_turn(
                workspace_id,
                'assistant',
                full_response,
                metadata={}
            )

            # Send done signal
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    response = Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


@app.route('/api/workspaces/<workspace_id>/conversation', methods=['GET'])
def get_conversation(workspace_id):
    """Get conversation history for a workspace."""
    limit = request.args.get('limit', type=int)
    history = workspace_manager.get_conversation_history(workspace_id, limit=limit)

    return jsonify({'conversation': history})


@app.route('/api/workspaces/<workspace_id>/conversation', methods=['DELETE'])
def clear_conversation(workspace_id):
    """Clear conversation history for a workspace."""
    success = workspace_manager.clear_conversation_history(workspace_id)

    if not success:
        return jsonify({'error': 'Workspace not found'}), 404

    return jsonify({'message': 'Conversation cleared successfully'})


# ============================================================================
# System API
# ============================================================================

@app.route('/api/system/status', methods=['GET'])
def system_status():
    """Get system status and statistics."""
    return jsonify({
        'status': 'operational' if Config.is_configured() else 'not_configured',
        'configured': Config.is_configured(),
        'vector_store': vector_store.get_stats() if vector_store else {'total_chunks': 0, 'total_documents': 0},
        'workspaces_count': len(workspace_manager.list_workspaces()),
        'global_docs_count': len(global_docs_manager.list_documents())
    })


# ============================================================================
# Settings API
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings status (without revealing API keys)."""
    return jsonify({
        'configured': Config.is_configured(),
        'anthropic_configured': bool(Config.ANTHROPIC_API_KEY)
    })


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save API keys and reinitialize modules."""
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    anthropic_key = data.get('anthropic_api_key')

    # Validate Anthropic key is provided (required)
    if anthropic_key is not None and not anthropic_key.strip():
        # Allow empty string to clear the key, but warn
        pass

    # Save keys to config file
    Config.save_api_keys(
        anthropic_key=anthropic_key if anthropic_key is not None else None
    )

    # Reinitialize AI modules with new keys
    success = initialize_ai_modules()

    if success:
        # Reload documents into vector store
        reload_all_documents_to_vector_store()

    return jsonify({
        'success': True,
        'configured': Config.is_configured(),
        'anthropic_configured': bool(Config.ANTHROPIC_API_KEY),
        'message': 'Settings saved successfully' if success else 'Settings saved but API key may be invalid'
    })


@app.route('/api/settings/validate', methods=['POST'])
def validate_api_key():
    """Validate an API key without saving it."""
    data = request.json

    if not data or 'anthropic_api_key' not in data:
        return jsonify({'error': 'API key is required'}), 400

    api_key = data['anthropic_api_key']

    if not api_key or not api_key.strip():
        return jsonify({'valid': False, 'error': 'API key cannot be empty'}), 400

    # Try to validate the key by making a simple API call
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        # Make a minimal API call to validate the key
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        return jsonify({'valid': True, 'message': 'API key is valid'})
    except Exception as e:
        error_msg = str(e)
        if 'authentication' in error_msg.lower() or 'api key' in error_msg.lower():
            return jsonify({'valid': False, 'error': 'Invalid API key'}), 400
        else:
            return jsonify({'valid': False, 'error': f'Validation failed: {error_msg}'}), 400


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    # threaded=True is important for SSE streaming to work properly
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG,
        threaded=True
    )
