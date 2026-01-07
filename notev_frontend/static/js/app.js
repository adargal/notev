// Notev Frontend Application

const API_BASE = '/api';
let currentWorkspace = null;
let isConfigured = false;

// ============================================================================
// Utility Functions
// ============================================================================

function formatTimestamp(isoString) {
    /**
     * Format ISO timestamp to DD/MM/YYYY HH:MM format (24-hour, no seconds)
     * Using Tel Aviv timezone (Asia/Jerusalem)
     */
    const date = new Date(isoString);

    // Convert to Tel Aviv time
    const telAvivDate = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Jerusalem' }));

    const day = String(telAvivDate.getDate()).padStart(2, '0');
    const month = String(telAvivDate.getMonth() + 1).padStart(2, '0');
    const year = telAvivDate.getFullYear();

    const hours = String(telAvivDate.getHours()).padStart(2, '0');
    const minutes = String(telAvivDate.getMinutes()).padStart(2, '0');

    return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    setupEventListeners();
    await checkConfiguration();
    loadWorkspaces();
    loadGlobalDocuments();
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Toggle Events visibility
    document.getElementById('toggle-events-btn').addEventListener('click', () => {
        const toggleBtn = document.getElementById('toggle-events-btn');
        const eventsContent = document.getElementById('events-content');

        const isCollapsed = toggleBtn.classList.toggle('collapsed');
        eventsContent.classList.toggle('collapsed');

        toggleBtn.textContent = isCollapsed ? '▶ Other Events' : '▼ Other Events';
    });

    // Workspace creation
    document.getElementById('new-workspace-btn').addEventListener('click', () => {
        document.getElementById('new-workspace-modal').style.display = 'block';
    });

    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('new-workspace-modal').style.display = 'none';
    });

    document.getElementById('new-workspace-form').addEventListener('submit', handleCreateWorkspace);

    // Document uploads
    document.getElementById('upload-global-doc-btn').addEventListener('click', () => {
        document.getElementById('global-doc-upload').click();
    });

    document.getElementById('upload-workspace-doc-btn').addEventListener('click', () => {
        document.getElementById('workspace-doc-upload').click();
    });

    document.getElementById('global-doc-upload').addEventListener('change', handleGlobalDocUpload);
    document.getElementById('workspace-doc-upload').addEventListener('change', handleWorkspaceDocUpload);

    // Chat
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Clear conversation
    document.getElementById('clear-conversation-btn').addEventListener('click', clearConversation);

    // Document preview modal
    document.getElementById('close-preview').addEventListener('click', () => {
        document.getElementById('document-preview-modal').style.display = 'none';
    });

    // Settings modal
    document.getElementById('settings-btn').addEventListener('click', openSettingsModal);
    document.getElementById('close-settings').addEventListener('click', closeSettingsModal);
    document.getElementById('settings-form').addEventListener('submit', handleSaveSettings);
    document.getElementById('validate-key-btn').addEventListener('click', handleValidateKey);
    document.getElementById('clear-keys-btn').addEventListener('click', handleClearKeys);
    document.getElementById('config-banner-btn').addEventListener('click', openSettingsModal);

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        const workspaceModal = document.getElementById('new-workspace-modal');
        const previewModal = document.getElementById('document-preview-modal');
        const settingsModal = document.getElementById('settings-modal');
        if (e.target === workspaceModal) {
            workspaceModal.style.display = 'none';
        }
        if (e.target === previewModal) {
            previewModal.style.display = 'none';
        }
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });
}

// ============================================================================
// Workspace Management
// ============================================================================

async function loadWorkspaces() {
    try {
        const response = await fetch(`${API_BASE}/workspaces`);
        const data = await response.json();

        const currentContainer = document.getElementById('current-workspace-container');
        const workspacesList = document.getElementById('workspaces-list');

        currentContainer.innerHTML = '';
        workspacesList.innerHTML = '';

        data.workspaces.forEach(workspace => {
            const item = createWorkspaceItem(workspace);
            if (currentWorkspace && workspace.id === currentWorkspace.id) {
                currentContainer.appendChild(item);
            } else {
                workspacesList.appendChild(item);
            }
        });
    } catch (error) {
        console.error('Error loading workspaces:', error);
        alert('Failed to load events');
    }
}

function createWorkspaceItem(workspace) {
    const div = document.createElement('div');
    div.className = 'workspace-item';
    div.dataset.workspaceId = workspace.id;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'workspace-item-content';

    const h4 = document.createElement('h4');
    h4.textContent = workspace.name;

    const p = document.createElement('p');
    p.textContent = workspace.description || 'No description';

    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'workspace-item-timestamp';
    timestampSpan.textContent = formatTimestamp(workspace.created_at);

    contentDiv.appendChild(h4);
    contentDiv.appendChild(timestampSpan);
    contentDiv.appendChild(p);

    const deleteBtn = document.createElement('span');
    deleteBtn.className = 'workspace-item-delete';
    deleteBtn.textContent = '×';
    deleteBtn.title = 'Delete event';
    deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteWorkspace(workspace.id, workspace.name);
    });

    div.appendChild(contentDiv);
    div.appendChild(deleteBtn);

    contentDiv.addEventListener('click', () => selectWorkspace(workspace.id));

    return div;
}

async function handleCreateWorkspace(e) {
    e.preventDefault();

    const name = document.getElementById('workspace-name-input').value;
    const description = document.getElementById('workspace-desc-input').value;

    try {
        const response = await fetch(`${API_BASE}/workspaces`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description })
        });

        if (!response.ok) throw new Error('Failed to create event');

        const data = await response.json();

        // Close modal and reset form
        document.getElementById('new-workspace-modal').style.display = 'none';
        document.getElementById('new-workspace-form').reset();

        // Reload workspaces
        await loadWorkspaces();

        // Select the new workspace
        selectWorkspace(data.workspace.id);

    } catch (error) {
        console.error('Error creating workspace:', error);
        alert('Failed to create event');
    }
}

async function selectWorkspace(workspaceId) {
    try {
        const response = await fetch(`${API_BASE}/workspaces/${workspaceId}`);
        const data = await response.json();

        currentWorkspace = data.workspace;

        // Reload workspaces to move current to top container
        await loadWorkspaces();

        document.getElementById('no-workspace-message').style.display = 'none';
        document.getElementById('workspace-info').style.display = 'block';
        document.getElementById('chat-container').style.display = 'flex';

        document.getElementById('workspace-name').textContent = currentWorkspace.name;
        document.getElementById('workspace-description').textContent =
            currentWorkspace.description || 'No description';

        // Enable workspace document upload
        document.getElementById('upload-workspace-doc-btn').disabled = false;

        // Load workspace documents and conversation
        loadWorkspaceDocuments();
        loadConversation();

    } catch (error) {
        console.error('Error selecting workspace:', error);
        alert('Failed to load event');
    }
}

async function deleteWorkspace(workspaceId, workspaceName) {
    if (!confirm(`Are you sure you want to delete event "${workspaceName}"?\n\nThis will delete all documents and conversation history in this event.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/workspaces/${workspaceId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete event');

        // If the deleted workspace was selected, clear the chat area
        if (currentWorkspace && currentWorkspace.id === workspaceId) {
            currentWorkspace = null;
            document.getElementById('no-workspace-message').style.display = 'flex';
            document.getElementById('workspace-info').style.display = 'none';
            document.getElementById('chat-container').style.display = 'none';
            document.getElementById('upload-workspace-doc-btn').disabled = true;
            document.getElementById('workspace-docs-list').innerHTML = '';
        }

        // Reload workspaces
        await loadWorkspaces();

    } catch (error) {
        console.error('Error deleting workspace:', error);
        alert('Failed to delete event');
    }
}

// ============================================================================
// Document Management
// ============================================================================

async function loadGlobalDocuments() {
    try {
        const response = await fetch(`${API_BASE}/global-documents`);
        const data = await response.json();

        const docsList = document.getElementById('global-docs-list');
        docsList.innerHTML = '';

        data.documents.forEach(doc => {
            const item = createDocItem(doc, 'global');
            docsList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading global documents:', error);
    }
}

async function loadWorkspaceDocuments() {
    if (!currentWorkspace) return;

    try {
        const response = await fetch(`${API_BASE}/workspaces/${currentWorkspace.id}/documents`);
        const data = await response.json();

        const docsList = document.getElementById('workspace-docs-list');
        docsList.innerHTML = '';

        data.documents.forEach(doc => {
            const item = createDocItem(doc, 'workspace');
            docsList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading workspace documents:', error);
    }
}

function createDocItem(doc, type) {
    const div = document.createElement('div');
    div.className = 'doc-item';

    const nameSpan = document.createElement('span');
    nameSpan.className = 'doc-item-name';
    nameSpan.textContent = doc.original_filename || doc.filename;
    nameSpan.title = 'Click to preview document';
    nameSpan.style.cursor = 'pointer';
    nameSpan.addEventListener('click', () => previewDocument(doc, type));

    const deleteSpan = document.createElement('span');
    deleteSpan.className = 'doc-item-delete';
    deleteSpan.textContent = '×';
    deleteSpan.title = 'Delete document';
    deleteSpan.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteDocument(doc.id, type);
    });

    div.appendChild(nameSpan);
    div.appendChild(deleteSpan);

    return div;
}

async function handleGlobalDocUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/global-documents`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        await loadGlobalDocuments();
        e.target.value = ''; // Reset file input

        alert('Global document uploaded successfully');

    } catch (error) {
        console.error('Error uploading global document:', error);
        alert(`Failed to upload document: ${error.message}`);
    }
}

async function handleWorkspaceDocUpload(e) {
    const file = e.target.files[0];
    if (!file || !currentWorkspace) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/workspaces/${currentWorkspace.id}/documents`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        await loadWorkspaceDocuments();
        e.target.value = ''; // Reset file input

        alert('Workspace document uploaded successfully');

    } catch (error) {
        console.error('Error uploading workspace document:', error);
        alert(`Failed to upload document: ${error.message}`);
    }
}

async function previewDocument(doc, type) {
    try {
        let url;
        if (type === 'global') {
            url = `${API_BASE}/global-documents/${doc.id}/content`;
        } else {
            url = `${API_BASE}/workspaces/${currentWorkspace.id}/documents/${doc.id}/content`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch document content');

        const data = await response.json();

        // Update modal content
        document.getElementById('preview-doc-name').textContent = doc.original_filename || doc.filename;

        const infoDiv = document.getElementById('preview-doc-info');
        infoDiv.innerHTML = `
            <strong>Type:</strong> ${data.file_type || 'Unknown'} |
            <strong>Chunks:</strong> ${data.num_chunks || 0} |
            <strong>Characters:</strong> ${data.total_chars || 0}
        `;

        const contentDiv = document.getElementById('preview-doc-content');
        contentDiv.textContent = data.full_text || 'No content available';

        // Detect RTL for preview content
        if (detectRTL(data.full_text || '')) {
            contentDiv.dir = 'rtl';
            contentDiv.style.textAlign = 'right';
        } else {
            contentDiv.dir = 'ltr';
            contentDiv.style.textAlign = 'left';
        }

        // Show modal
        document.getElementById('document-preview-modal').style.display = 'block';

    } catch (error) {
        console.error('Error previewing document:', error);
        alert('Failed to load document preview');
    }
}

async function deleteDocument(docId, type) {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
        let url;
        if (type === 'global') {
            url = `${API_BASE}/global-documents/${docId}`;
        } else {
            url = `${API_BASE}/workspaces/${currentWorkspace.id}/documents/${docId}`;
        }

        const response = await fetch(url, { method: 'DELETE' });

        if (!response.ok) throw new Error('Failed to delete document');

        if (type === 'global') {
            await loadGlobalDocuments();
        } else {
            await loadWorkspaceDocuments();
        }

    } catch (error) {
        console.error('Error deleting document:', error);
        alert('Failed to delete document');
    }
}

// ============================================================================
// Chat
// ============================================================================

async function loadConversation() {
    if (!currentWorkspace) return;

    try {
        const response = await fetch(`${API_BASE}/workspaces/${currentWorkspace.id}/conversation`);
        const data = await response.json();

        const messagesDiv = document.getElementById('messages');
        messagesDiv.innerHTML = '';

        data.conversation.forEach(turn => {
            appendMessage(turn.role, turn.content, turn.timestamp);
        });

        scrollToBottom();

    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

async function sendMessage() {
    if (!currentWorkspace) return;

    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message) return;

    // Clear input and add user message to UI
    input.value = '';
    appendMessage('user', message);

    // Disable send button and input
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    input.disabled = true;

    // Add thinking indicator
    const thinkingId = addThinkingIndicator();

    try {
        const response = await fetch(`${API_BASE}/workspaces/${currentWorkspace.id}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) throw new Error('Failed to send message');

        // Remove thinking indicator and create empty assistant message
        removeThinkingIndicator(thinkingId);
        const messageDiv = appendMessage('assistant', '');
        const contentDiv = messageDiv.querySelector('.message-content');

        // Stream the response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE format: "data: {...}\n\n"
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.text) {
                            fullText += data.text;
                            contentDiv.innerHTML = formatMessageContent(fullText);
                            // Update RTL direction as text comes in
                            if (detectRTL(fullText)) {
                                contentDiv.dir = 'rtl';
                                contentDiv.style.textAlign = 'right';
                            }
                            scrollToBottom();
                        }
                        if (data.error) {
                            console.error('Stream error:', data.error);
                            contentDiv.innerHTML = formatMessageContent(`Error: ${data.error}`);
                        }
                    } catch (e) {
                        // Ignore JSON parse errors for incomplete data
                    }
                }
            }
        }

        scrollToBottom();

    } catch (error) {
        console.error('Error sending message:', error);
        removeThinkingIndicator(thinkingId);
        alert('Failed to send message');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
        input.disabled = false;
        input.focus();
    }
}

function formatMessageContent(content) {
    // Escape HTML to prevent XSS
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    let formatted = escapeHtml(content);

    // Convert markdown-style formatting
    // Bold: **text** or __text__
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/_(.+?)_/g, '<em>$1</em>');

    // Code blocks: ```code```
    formatted = formatted.replace(/```(.+?)```/gs, '<pre><code>$1</code></pre>');

    // Inline code: `code`
    formatted = formatted.replace(/`(.+?)`/g, '<code>$1</code>');

    // Headers: ## Header
    formatted = formatted.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    formatted = formatted.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    formatted = formatted.replace(/^# (.+)$/gm, '<h2>$1</h2>');

    // Lists: - item or * item
    formatted = formatted.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Numbered lists: 1. item
    formatted = formatted.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Line breaks: Convert all newlines to spaces for maximum density
    // Only actual structural elements (headers, lists, code blocks) create spacing
    formatted = formatted.replace(/\n+/g, ' ');
    // Clean up multiple spaces
    formatted = formatted.replace(/\s+/g, ' ');

    return formatted;
}

function detectRTL(text) {
    // Hebrew Unicode range: \u0590-\u05FF
    // Arabic Unicode range: \u0600-\u06FF
    const rtlPattern = /[\u0590-\u05FF\u0600-\u06FF]/;
    return rtlPattern.test(text);
}

function appendMessage(role, content, timestamp) {
    const messagesDiv = document.getElementById('messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    headerDiv.textContent = role === 'user' ? 'You' : 'Notev';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Format content with proper line breaks and basic markdown-style formatting
    const formattedContent = formatMessageContent(content);
    contentDiv.innerHTML = formattedContent;

    // Detect and set RTL direction for Hebrew/Arabic text
    if (detectRTL(content)) {
        contentDiv.dir = 'rtl';
        contentDiv.style.textAlign = 'right';
    }

    messageDiv.appendChild(headerDiv);
    messageDiv.appendChild(contentDiv);

    // Always add timestamp - use provided timestamp or current time
    const metadataDiv = document.createElement('div');
    metadataDiv.className = 'message-metadata';
    const displayTimestamp = timestamp || new Date().toISOString();
    metadataDiv.textContent = formatTimestamp(displayTimestamp);
    messageDiv.appendChild(metadataDiv);

    messagesDiv.appendChild(messageDiv);

    // Return the message div for streaming updates
    return messageDiv;
}

function scrollToBottom() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addThinkingIndicator() {
    const messagesDiv = document.getElementById('messages');

    const thinkingDiv = document.createElement('div');
    const thinkingId = 'thinking-' + Date.now();
    thinkingDiv.id = thinkingId;
    thinkingDiv.className = 'message assistant thinking';

    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    headerDiv.textContent = 'Notev';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content thinking-content';
    contentDiv.innerHTML = '<div class="thinking-spinner"></div><span class="thinking-text">Analyzing documents and formulating response...</span>';

    thinkingDiv.appendChild(headerDiv);
    thinkingDiv.appendChild(contentDiv);
    messagesDiv.appendChild(thinkingDiv);

    scrollToBottom();

    return thinkingId;
}

function removeThinkingIndicator(thinkingId) {
    const thinkingDiv = document.getElementById(thinkingId);
    if (thinkingDiv) {
        thinkingDiv.remove();
    }
}

async function clearConversation() {
    if (!currentWorkspace) return;

    if (!confirm('Are you sure you want to clear the conversation history?')) return;

    try {
        const response = await fetch(`${API_BASE}/workspaces/${currentWorkspace.id}/conversation`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to clear conversation');

        document.getElementById('messages').innerHTML = '';

    } catch (error) {
        console.error('Error clearing conversation:', error);
        alert('Failed to clear conversation');
    }
}

// ============================================================================
// Settings Management
// ============================================================================

async function checkConfiguration() {
    try {
        const response = await fetch(`${API_BASE}/settings`);
        const data = await response.json();

        isConfigured = data.configured;

        const configBanner = document.getElementById('config-banner');
        if (!isConfigured) {
            configBanner.style.display = 'block';
            document.body.classList.add('has-config-banner');
            // Auto-open settings on first visit if not configured
            openSettingsModal();
        } else {
            configBanner.style.display = 'none';
            document.body.classList.remove('has-config-banner');
        }

        return data;
    } catch (error) {
        console.error('Error checking configuration:', error);
        return { configured: false };
    }
}

function openSettingsModal() {
    const modal = document.getElementById('settings-modal');
    modal.style.display = 'block';

    // Load current settings status
    loadSettingsStatus();
}

function closeSettingsModal() {
    document.getElementById('settings-modal').style.display = 'none';
    // Clear status messages
    document.getElementById('anthropic-status').className = 'api-status';
}

async function loadSettingsStatus() {
    try {
        const response = await fetch(`${API_BASE}/settings`);
        const data = await response.json();

        const anthropicStatus = document.getElementById('anthropic-status');

        if (data.anthropic_configured) {
            anthropicStatus.textContent = 'API key is configured';
            anthropicStatus.className = 'api-status configured';
        } else {
            anthropicStatus.className = 'api-status';
        }

    } catch (error) {
        console.error('Error loading settings status:', error);
    }
}

async function handleValidateKey() {
    const apiKeyInput = document.getElementById('anthropic-api-key');
    const apiKey = apiKeyInput.value.trim();
    const statusDiv = document.getElementById('anthropic-status');
    const validateBtn = document.getElementById('validate-key-btn');

    if (!apiKey) {
        statusDiv.textContent = 'Please enter an API key to validate';
        statusDiv.className = 'api-status error';
        return;
    }

    validateBtn.disabled = true;
    validateBtn.textContent = 'Validating...';
    statusDiv.textContent = 'Validating API key...';
    statusDiv.className = 'api-status configured';

    try {
        const response = await fetch(`${API_BASE}/settings/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ anthropic_api_key: apiKey })
        });

        const data = await response.json();

        if (data.valid) {
            statusDiv.textContent = 'API key is valid!';
            statusDiv.className = 'api-status success';
        } else {
            statusDiv.textContent = data.error || 'Invalid API key';
            statusDiv.className = 'api-status error';
        }

    } catch (error) {
        console.error('Error validating API key:', error);
        statusDiv.textContent = 'Error validating API key';
        statusDiv.className = 'api-status error';
    } finally {
        validateBtn.disabled = false;
        validateBtn.textContent = 'Validate Key';
    }
}

async function handleSaveSettings(e) {
    e.preventDefault();

    const anthropicKey = document.getElementById('anthropic-api-key').value.trim();
    const anthropicStatus = document.getElementById('anthropic-status');

    // Check if at least anthropic key is being set (if not already configured)
    if (!anthropicKey && !isConfigured) {
        anthropicStatus.textContent = 'Anthropic API key is required';
        anthropicStatus.className = 'api-status error';
        return;
    }

    // Build settings object - only include key if it has a value
    const settings = {};
    if (anthropicKey) {
        settings.anthropic_api_key = anthropicKey;
    }

    try {
        const response = await fetch(`${API_BASE}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });

        const data = await response.json();

        if (data.success) {
            alert('Settings saved successfully!');
            isConfigured = data.configured;

            // Clear input field
            document.getElementById('anthropic-api-key').value = '';

            // Update banner visibility
            const configBanner = document.getElementById('config-banner');
            if (isConfigured) {
                configBanner.style.display = 'none';
                document.body.classList.remove('has-config-banner');
            }

            // Close modal and reload settings status
            closeSettingsModal();

        } else {
            anthropicStatus.textContent = data.error || 'Failed to save settings';
            anthropicStatus.className = 'api-status error';
        }

    } catch (error) {
        console.error('Error saving settings:', error);
        anthropicStatus.textContent = 'Error saving settings';
        anthropicStatus.className = 'api-status error';
    }
}

async function handleClearKeys() {
    if (!confirm('Are you sure you want to clear the API key?\n\nThis will disable the chat functionality until a new key is configured.')) {
        return;
    }

    const anthropicStatus = document.getElementById('anthropic-status');

    try {
        const response = await fetch(`${API_BASE}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                anthropic_api_key: ''
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('API key cleared successfully.');
            isConfigured = false;

            // Show config banner
            const configBanner = document.getElementById('config-banner');
            configBanner.style.display = 'block';
            document.body.classList.add('has-config-banner');

            // Reload settings status
            loadSettingsStatus();
        } else {
            anthropicStatus.textContent = data.error || 'Failed to clear key';
            anthropicStatus.className = 'api-status error';
        }

    } catch (error) {
        console.error('Error clearing key:', error);
        anthropicStatus.textContent = 'Error clearing key';
        anthropicStatus.className = 'api-status error';
    }
}
