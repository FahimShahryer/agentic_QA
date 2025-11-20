// API Base URL
const API_BASE = '/api';

// State
let sessionId = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const documentsList = document.getElementById('documentsList');
const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const questionForm = document.getElementById('questionForm');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initSession();
    setupDragAndDrop();
    setupFileInput();
});

// Session Management
async function initSession() {
    try {
        const response = await fetch(`${API_BASE}/session`, {
            method: 'POST'
        });
        const data = await response.json();
        sessionId = data.session_id;
        console.log('Session created:', sessionId);
    } catch (error) {
        console.error('Failed to create session:', error);
        showError('Failed to initialize session. Please refresh the page.');
    }
}

async function endSession() {
    if (!sessionId) return;

    if (!confirm('This will delete all uploaded documents and chat history. Continue?')) {
        return;
    }

    try {
        await fetch(`${API_BASE}/session/${sessionId}`, {
            method: 'DELETE'
        });

        // Reset UI
        resetUI();

        // Create new session
        await initSession();

    } catch (error) {
        console.error('Failed to end session:', error);
        showError('Failed to end session.');
    }
}

function resetUI() {
    // Clear documents list
    documentsList.innerHTML = '<li class="no-docs">No documents uploaded</li>';

    // Clear chat
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>Welcome!</h2>
            <p>Upload PDF documents and start asking questions.</p>
            <p>I'll provide answers with citations to the source pages.</p>
        </div>
    `;

    // Disable input
    questionInput.disabled = true;
    sendBtn.disabled = true;
}

// File Upload
function setupDragAndDrop() {
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = Array.from(e.dataTransfer.files).filter(
            f => f.type === 'application/pdf'
        );

        if (files.length > 0) {
            uploadFiles(files);
        } else {
            showError('Please upload PDF files only.');
        }
    });
}

function setupFileInput() {
    fileInput.addEventListener('change', () => {
        const files = Array.from(fileInput.files);
        if (files.length > 0) {
            uploadFiles(files);
        }
        fileInput.value = '';
    });
}

async function uploadFiles(files) {
    if (!sessionId) {
        showError('No active session. Please refresh the page.');
        return;
    }

    // Show progress
    uploadArea.classList.add('hidden');
    uploadProgress.classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('session_id', sessionId);

        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const data = await response.json();

        // Update documents list
        updateDocumentsList(data.documents);

        // Enable chat
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();

        // Show success in chat
        addSystemMessage(`Successfully uploaded ${files.length} document(s). Created ${data.total_chunks} chunks. You can now ask questions!`);

    } catch (error) {
        console.error('Upload failed:', error);
        showError(error.message);
    } finally {
        uploadArea.classList.remove('hidden');
        uploadProgress.classList.add('hidden');
    }
}

function updateDocumentsList(documents) {
    if (documents.length === 0) {
        documentsList.innerHTML = '<li class="no-docs">No documents uploaded</li>';
        return;
    }

    documentsList.innerHTML = documents.map(doc => `
        <li>
            <span class="doc-icon">📄</span>
            <span>${doc}</span>
        </li>
    `).join('');
}

// Chat Functions
async function askQuestion(event) {
    event.preventDefault();

    const question = questionInput.value.trim();
    if (!question || !sessionId) return;

    // Add user message
    addMessage(question, 'user');

    // Clear input
    questionInput.value = '';

    // Show loading
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch(`${API_BASE}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                question: question
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get answer');
        }

        const data = await response.json();

        // Remove loading
        removeLoadingMessage(loadingId);

        // Add assistant message
        addMessage(data.answer, 'assistant', data.references);

    } catch (error) {
        console.error('Question failed:', error);
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'assistant');
    }
}

function addMessage(content, role, references = '') {
    // Remove welcome message if present
    const welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    let html = `<div class="message-content">${formatMessage(content)}`;

    if (references && role === 'assistant') {
        html += `<div class="message-references">${formatReferences(references)}</div>`;
    }

    html += '</div>';
    messageDiv.innerHTML = html;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addSystemMessage(content) {
    const welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content" style="background: #e8f5e9; border-color: #c8e6c9;">
            ${content}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addLoadingMessage() {
    const id = 'loading-' + Date.now();

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant loading';
    messageDiv.id = id;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="spinner"></div>
            <span>Thinking...</span>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return id;
}

function removeLoadingMessage(id) {
    const loading = document.getElementById(id);
    if (loading) {
        loading.remove();
    }
}

function formatMessage(content) {
    // Convert markdown-like formatting
    return content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[([\d]+)\]/g, '<strong>[$1]</strong>');
}

function formatReferences(references) {
    if (!references) return '';

    return references
        .replace(/---/g, '')
        .replace(/\*\*References:\*\*/g, '<strong>References:</strong>')
        .replace(/\n/g, '<br>')
        .trim();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Clear Chat
async function clearChat() {
    if (!sessionId) return;

    try {
        await fetch(`${API_BASE}/history/${sessionId}`, {
            method: 'DELETE'
        });

        // Clear chat messages but keep welcome or show cleared message
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h2>Chat Cleared</h2>
                <p>Your documents are still available.</p>
                <p>Ask a new question to continue.</p>
            </div>
        `;

    } catch (error) {
        console.error('Failed to clear chat:', error);
        showError('Failed to clear chat history.');
    }
}

// Error Handling
function showError(message) {
    alert(message);
}

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (sessionId) {
        // Use sendBeacon for reliable cleanup
        navigator.sendBeacon(`${API_BASE}/session/${sessionId}`, '');
    }
});
