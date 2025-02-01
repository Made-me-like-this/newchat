const roomId = '{{ room.id }}';
const userId = '{{ request.user.id }}';
const username = '{{ request.user.username }}';

class ChatConnection {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        this.isConnecting = false;
        this.connect();
    }

    connect() {
        if (this.isConnecting) return;
        this.isConnecting = true;

        this.socket = new WebSocket(
            `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/${roomId}/`
        );

        this.socket.onopen = this.handleOpen.bind(this);
        this.socket.onclose = this.handleClose.bind(this);
        this.socket.onmessage = this.handleMessage.bind(this);
        this.socket.onerror = this.handleError.bind(this);
    }

    handleOpen(e) {
        console.log('WebSocket connection established');
        this.isConnecting = false;
        this.reconnectAttempts = 0;

        showNotification("Connected to chat room", 'success');

        // Send join notification
        this.send({
            type: 'join',
            username: username
        });
    }

    handleClose(e) {
        console.error('WebSocket connection closed');
        this.isConnecting = false;

        showNotification("Disconnected from chat room. Trying to reconnect...", 'error');

        // Attempt to reconnect with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
            this.reconnectAttempts++;

            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay/1000}s...`);

            setTimeout(() => this.connect(), delay);
        } else {
            showNotification("Connection lost. Please refresh the page.", 'error');
        }
    }

    handleMessage(e) {
        try {
            const data = JSON.parse(e.data);

            switch(data.type) {
                case 'chat':
                    addMessage(data.message, data.user_id, data.username);
                    break;
                case 'join':
                    showNotification(`${data.username} joined the room`, 'success');
                    break;
                case 'leave':
                    showNotification(`${data.username} left the room`, 'info');
                    break;
                case 'typing':
                    handleTypingIndicator(data.username, data.is_typing);
                    break;
                case 'error':
                    showNotification(data.message, 'error');
                    break;
                default:
                    console.log('Unknown message type:', data.type);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    handleError(error) {
        console.error('WebSocket error:', error);
        showNotification("Connection error occurred", 'error');
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify(data));
            } catch (error) {
                console.error('Error sending message:', error);
                showNotification("Failed to send message", 'error');
            }
        } else {
            console.error('WebSocket is not connected');
            showNotification('Connection lost. Please refresh the page.', 'error');
        }
    }

    close() {
        if (this.socket) {
            this.socket.close();
        }
    }
}
