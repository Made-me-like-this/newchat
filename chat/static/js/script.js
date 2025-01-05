const chatButton = document.getElementById('chat-button');
const chatContainer = document.getElementById('chat-container');
const sendButton = document.getElementById('send-button');
const messages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const fileInput = document.getElementById('file-input');

// Fetch and display chat history
async function fetchMessages() {
    const response = await fetch('/api/chat/messages/');
    const data = await response.json();
    messages.innerHTML = '';
    data.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.textContent = msg.message || `File: ${msg.file}`;
        messages.appendChild(msgDiv);
    });
}

// Send a new message
sendButton.addEventListener('click', async () => {
    const message = messageInput.value;
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('sender', 'User'); // Replace with dynamic sender info if needed
    if (message) formData.append('message', message);
    if (file) formData.append('file', file);

    const response = await fetch('/api/chat/messages/create/', {
        method: 'POST',
        body: formData,
    });

    if (response.ok) {
        fetchMessages();
        messageInput.value = '';
        fileInput.value = null;
    } else {
        alert('Failed to send message.');
    }
});

// Initial fetch
fetchMessages();
