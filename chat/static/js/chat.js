// Typing indicator handling
let typingTimeout;
function handleTypingIndicator(username, isTyping) {
    const typingIndicator = document.getElementById('typingIndicator');
    if (!typingIndicator) return;

    if (isTyping && username !== '{{ request.user.username }}') {
        typingIndicator.textContent = `${username} is typing...`;
        typingIndicator.classList.remove('hidden');
    } else {
        typingIndicator.classList.add('hidden');
    }
}

function showNotification(message, type) {
    const backgroundColors = {
        success: "#48BB78",
        error: "#F56565",
        info: "#6B46C1"
    };

    Toastify({
        text: message,
        duration: 3000,
        backgroundColor: backgroundColors[type] || backgroundColors.info,
        className: 'chat-notification',
        position: 'top-right',
        stopOnFocus: true
    }).showToast();
}

function addMessage(message, senderId, senderUsername) {
    const container = document.getElementById('messageContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex flex-col mb-4';

    const isOwn = senderId === userId;
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
        <div class="message ${isOwn ? 'own' : 'other'} rounded-lg p-3 mb-1">
            ${message}
        </div>
        <div class="text-xs text-gray-500 ${isOwn ? 'text-right' : ''}">
            ${senderUsername} - ${timestamp}
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// Initialize chat connection
const chatConnection = new ChatConnection();

// Form Handler
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');

chatForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const message = messageInput.value.trim();

    if (message) {
        chatConnection.send({
            type: 'chat',
            message: message,
            user_id: userId,
            username: username
        });
        messageInput.value = '';
    }
});

// Typing indicator
let isTyping = false;
messageInput.addEventListener('input', function() {
    if (!isTyping) {
        isTyping = true;
        chatConnection.send({
            type: 'typing',
            is_typing: true,
            username: username
        });
    }

    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        isTyping = false;
        chatConnection.send({
            type: 'typing',
            is_typing: false,
            username: username
        });
    }, 1000);
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    chatConnection.send({
        type: 'leave',
        username: username
    });
    chatConnection.close();
});
