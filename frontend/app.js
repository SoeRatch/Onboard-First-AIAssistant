/**
 * Occams Advisory AI Assistant - Frontend Application
 * =====================================================
 * Handles chat interactions, onboarding, and API communication.
 */

// ============================================
// State Management
// ============================================

const state = {
    sessionId: generateSessionId(),
    messageCount: 0,
    onboarding: {
        name: null,
        email: null,
        phone: null,
        completed: false
    },
    messages: []
};

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// ============================================
// DOM Elements
// ============================================

const elements = {
    // Onboarding
    nameInput: document.getElementById('userName'),
    emailInput: document.getElementById('userEmail'),
    phoneInput: document.getElementById('userPhone'),
    nameStatus: document.getElementById('nameStatus'),
    emailStatus: document.getElementById('emailStatus'),
    phoneStatus: document.getElementById('phoneStatus'),
    emailError: document.getElementById('emailError'),
    phoneError: document.getElementById('phoneError'),
    submitBtn: document.getElementById('submitOnboarding'),
    progressBar: document.getElementById('progressBar'),
    onboardingForm: document.getElementById('onboardingForm'),
    onboardingComplete: document.getElementById('onboardingComplete'),
    welcomeMessage: document.getElementById('welcomeMessage'),

    // Chat
    chatMessages: document.getElementById('chatMessages'),
    chatForm: document.getElementById('chatForm'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    typingIndicator: document.getElementById('typingIndicator')
};

// ============================================
// Validation
// ============================================

const validators = {
    email: (value) => {
        const pattern = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$/;
        return pattern.test(value);
    },

    phone: (value) => {
        // Remove formatting characters
        const cleaned = value.replace(/[\s\-\.\(\)\+]/g, '');
        // Should be 10-11 digits
        return /^\d{10,11}$/.test(cleaned);
    },

    name: (value) => {
        return value.trim().length >= 2;
    }
};

// ============================================
// Onboarding Logic
// ============================================

function updateOnboardingField(field, value, isValid) {
    const statusEl = elements[`${field}Status`];
    const inputEl = elements[`${field}Input`];
    const errorEl = elements[`${field}Error`];

    if (value.trim() === '') {
        statusEl.className = 'field-status';
        inputEl.className = '';
        if (errorEl) errorEl.textContent = '';
        return;
    }

    if (isValid) {
        statusEl.className = 'field-status valid';
        inputEl.className = 'valid';
        if (errorEl) errorEl.textContent = '';
        state.onboarding[field] = value.trim();
    } else {
        statusEl.className = 'field-status invalid';
        inputEl.className = 'invalid';
        state.onboarding[field] = null;
    }

    updateProgress();
    updateSubmitButton();
}

function updateProgress() {
    let completed = 0;
    if (state.onboarding.name) completed++;
    if (state.onboarding.email) completed++;
    if (state.onboarding.phone) completed++;

    const percentage = (completed / 3) * 100;
    elements.progressBar.style.width = `${percentage}%`;
}

function updateSubmitButton() {
    const allValid = state.onboarding.name &&
        state.onboarding.email &&
        state.onboarding.phone;
    elements.submitBtn.disabled = !allValid;
}

async function submitOnboarding() {
    if (!state.onboarding.name || !state.onboarding.email || !state.onboarding.phone) {
        return;
    }

    elements.submitBtn.disabled = true;
    elements.submitBtn.textContent = 'Submitting...';

    try {
        const response = await fetch('/api/onboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: state.onboarding.name,
                email: state.onboarding.email,
                phone: state.onboarding.phone,
                session_id: state.sessionId
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            state.onboarding.completed = true;
            showOnboardingComplete(data.message);

            // Add confirmation message to chat
            addMessage('assistant', `🎉 ${data.message} I'm now ready to provide you with personalized assistance.`);
        } else {
            // Handle validation errors
            const error = data.detail || 'An error occurred. Please try again.';
            showError(error);
            elements.submitBtn.disabled = false;
            elements.submitBtn.textContent = 'Complete Onboarding';
        }
    } catch (error) {
        console.error('Onboarding error:', error);
        showError('Connection error. Please try again.');
        elements.submitBtn.disabled = false;
        elements.submitBtn.textContent = 'Complete Onboarding';
    }
}

function showOnboardingComplete(message) {
    elements.onboardingForm.style.display = 'none';
    elements.onboardingComplete.style.display = 'block';
    elements.welcomeMessage.textContent = message || 'You\'re all set!';
}

function showError(message) {
    // Show error in a toast or alert
    alert(message);
}

// ============================================
// Chat Logic
// ============================================

function addMessage(role, content, sources = []) {
    state.messages.push({ role, content, timestamp: new Date().toISOString() });

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = role === 'assistant' ? '◈' : '👤';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Parse content (support basic markdown-like formatting)
    contentDiv.innerHTML = formatMessage(content);

    // Add sources if available
    if (sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.innerHTML = '📚 Sources: ' + sources.map(url =>
            `<a href="${url}" target="_blank">${new URL(url).pathname || 'Homepage'}</a>`
        ).join(', ');
        contentDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function formatMessage(text) {
    // Convert basic markdown-like syntax
    return text
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Line breaks
        .replace(/\n/g, '<br>')
        // Lists
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function showTyping(show) {
    elements.typingIndicator.style.display = show ? 'flex' : 'none';
}

async function sendMessage(message) {
    if (!message.trim()) return;

    // Add user message
    addMessage('user', message);
    state.messageCount++;

    // Clear input
    elements.chatInput.value = '';

    // Show typing indicator
    showTyping(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: state.sessionId,
                onboarding: state.onboarding,
                message_count: state.messageCount
            })
        });

        const data = await response.json();

        // Hide typing indicator
        showTyping(false);

        if (response.ok) {
            // Add assistant response
            addMessage('assistant', data.response, data.sources || []);

            // Update onboarding state if info was detected
            if (data.detected_info) {
                if (data.detected_info.name && !state.onboarding.name) {
                    elements.nameInput.value = data.detected_info.name;
                    updateOnboardingField('name', data.detected_info.name, true);
                }
                if (data.detected_info.email && !state.onboarding.email) {
                    elements.emailInput.value = data.detected_info.email;
                    updateOnboardingField('email', data.detected_info.email, validators.email(data.detected_info.email));
                }
                if (data.detected_info.phone && !state.onboarding.phone) {
                    elements.phoneInput.value = data.detected_info.phone;
                    updateOnboardingField('phone', data.detected_info.phone, validators.phone(data.detected_info.phone));
                }
            }
        } else {
            addMessage('assistant', 'I apologize, but I encountered an error. Please try again.');
        }
    } catch (error) {
        console.error('Chat error:', error);
        showTyping(false);
        addMessage('assistant', 'I\'m having trouble connecting. Please check your connection and try again.');
    }

    // Save chat history periodically
    if (state.messageCount % 5 === 0) {
        saveChatHistory();
    }
}

async function saveChatHistory() {
    try {
        await fetch(`/api/chat-history/${state.sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.messages)
        });
    } catch (error) {
        console.error('Failed to save chat history:', error);
    }
}

// ============================================
// Event Listeners
// ============================================

// Onboarding inputs
elements.nameInput.addEventListener('input', (e) => {
    updateOnboardingField('name', e.target.value, validators.name(e.target.value));
});

elements.emailInput.addEventListener('input', (e) => {
    const isValid = validators.email(e.target.value);
    updateOnboardingField('email', e.target.value, isValid);
    if (e.target.value && !isValid) {
        elements.emailError.textContent = 'Please enter a valid email address';
    }
});

elements.phoneInput.addEventListener('input', (e) => {
    const isValid = validators.phone(e.target.value);
    updateOnboardingField('phone', e.target.value, isValid);
    if (e.target.value && !isValid) {
        elements.phoneError.textContent = 'Please enter a valid phone number';
    }
});

elements.submitBtn.addEventListener('click', submitOnboarding);

// Chat form
elements.chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(elements.chatInput.value);
});

// Enter key to send (but allow Shift+Enter for newlines)
elements.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(elements.chatInput.value);
    }
});

// ============================================
// Initialize
// ============================================

console.log('🚀 Occams Advisory AI Assistant initialized');
console.log('Session ID:', state.sessionId);
