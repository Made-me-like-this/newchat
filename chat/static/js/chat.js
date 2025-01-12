document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.querySelector('.send-btn');
    const messagesContainer = document.querySelector('.messages-container');
    
    // Send message function
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Send message to Django backend
            fetch('/send-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    chat_id: getCurrentChatId()
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    appendMessage(message, true);
                    messageInput.value = '';
                }
            });
        }
    }

    // Append message to chat
    function appendMessage(message, isSelf) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isSelf ? 'message-self' : ''}`;
        
        messageDiv.innerHTML = `
            ${!isSelf ? '<img src="/static/images/avatar.jpg" class="avatar">' : ''}
            <div class="message-content">
                <p>${message}</p>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Get current chat ID
    function getCurrentChatId() {
        // This should be implemented based on your URL structure or data attributes
        return document.querySelector('.chat-messages').dataset.chatId;
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Chat item click handler
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', function() {
            const chatId = this.dataset.chatId;
            window.location.href = `/chat/${chatId}/`;
        });
    });
});
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/'
);

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    const messages = document.getElementById('chat-messages');

    const newMessage = document.createElement('div');
    newMessage.classList.add('chat-message');
    newMessage.innerHTML = `<span class="username">${data.username}</span>: <span class="message">${data.message}</span>`;

    messages.appendChild(newMessage);
    messages.scrollTop = messages.scrollHeight;
};

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};

document.querySelector('#chat-message-input').focus();

document.querySelector('#chat-message-input').onkeyup = function (e) {
    if (e.keyCode === 13) {
        document.querySelector('#chat-message-submit').click();
    }
};

document.querySelector('#chat-message-submit').onclick = function (e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;

    chatSocket.send(JSON.stringify({
        'message': message
    }));

    messageInputDom.value = '';
};

document.addEventListener('DOMContentLoaded', function() {
    const messageContainer = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.querySelector('input[name="message"]');
    const chatId = document.querySelector('[data-chat-id]').dataset.chatId;

    // Scroll to bottom of messages
    function scrollToBottom() {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    // Initialize WebSocket connection
    const chatSocket = new WebSocket(
        `ws://${window.location.host}/ws/chat/${chatId}/`
    );

    // Handle incoming messages
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'chat_message') {
            addMessage(data);
            scrollToBottom();
        }
    };

    // Add message to chat
    function addMessage(data) {
        const messageDiv = document.createElement('div');
        const currentUserId = document.querySelector('[data-user-id]').dataset.userId;
        const isSentMessage = data.sender_id === parseInt(currentUserId);
        
        messageDiv.className = `message ${isSentMessage ? 'message-sent' : 'message-received'}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${data.message}
            </div>
            <div class="message-meta">
                <span class="message-time">${formatTime(new Date())}</span>
                ${isSentMessage ? '<span class="message-status"><i class="fas fa-check"></i></span>' : ''}
            </div>
        `;
        
        messageContainer.appendChild(messageDiv);
    }

    // Format time for messages
    function formatTime(date) {
        return date.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });
    }

    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        
        if (message) {
            // Send message through WebSocket
            chatSocket.send(JSON.stringify({
                'message': message,
                'chat_id': chatId
            }));
            
            messageInput.value = '';
        }
    });

    // Initial scroll to bottom
    scrollToBottom();
});
