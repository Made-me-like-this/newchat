import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message, MessageReaction, PrivateChat, PrivateMessage
from .models import VoiceCall, Poll, PollVote, Whiteboard
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope["user"]

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

        # Send connection message
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': self.user.username
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Send disconnection message
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_leave',
                'username': self.user.username
            }
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'message')

        if message_type == 'message':
            message = text_data_json['message']
            # Save message to database
            saved_message = await self.save_message(message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.user.username,
                    'user_id': str(self.user.id),
                    'message_id': str(saved_message.id)
                }
            )
        elif message_type == 'delete_message':
            message_id = text_data_json['message_id']
            success = await self.delete_message(message_id)
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id
                    }
                )

        elif message_type == 'reaction':
            message_id = text_data_json['message_id']
            reaction_type = text_data_json['reaction_type']
            reaction = await self.save_reaction(message_id, reaction_type)
            if reaction:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_reaction',
                        'message_id': message_id,
                        'reaction_type': reaction_type,
                        'username': self.user.username,
                        'user_id': str(self.user.id)
                    }
                )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'message_id': event['message_id']
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'delete',
            'message_id': event['message_id']
        }))

    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'reaction_type': event['reaction_type'],
            'username': event['username'],
            'user_id': event['user_id']
        }))

    async def user_join(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'join',
            'username': event['username']
        }))

    async def user_leave(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'leave',
            'username': event['username']
        }))

    @database_sync_to_async
    def save_message(self, message):
        room = Room.objects.get(id=self.room_id)
        return Message.objects.create(
            room=room,
            user=self.user,
            content=message
        )

    @database_sync_to_async
    def delete_message(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            # Check if user has permission to delete
            if self.user == message.user or self.user == message.room.created_by:
                message.delete()
                return True
            return False
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def save_reaction(self, message_id, reaction_type):
        try:
            message = Message.objects.get(id=message_id)
            # Remove existing reaction from this user if any
            MessageReaction.objects.filter(
                message=message,
                user=self.user
            ).delete()

            # Create new reaction
            return MessageReaction.objects.create(
                message=message,
                user=self.user,
                reaction_type=reaction_type
            )
        except Message.DoesNotExist:
            return None

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'private_chat_{self.chat_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        # Save message to database
        await self.save_message(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.scope['user'].id,
                'sender_username': self.scope['user'].username
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username']
        }))

    @database_sync_to_async
    def save_message(self, message):
        chat = PrivateChat.objects.get(id=self.chat_id)
        return PrivateMessage.objects.create(
            chat=chat,
            sender=self.scope['user'],
            content=message
        )

class VideoChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'video_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Notify others that peer has left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'peer_disconnected',
                'peer_id': self.channel_name
            }
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'offer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_offer',
                    'offer': data['offer'],
                    'sender_channel_name': self.channel_name,
                }
            )
        elif message_type == 'answer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_answer',
                    'answer': data['answer'],
                    'sender_channel_name': self.channel_name,
                }
            )
        elif message_type == 'ice_candidate':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_ice_candidate',
                    'candidate': data['candidate'],
                    'sender_channel_name': self.channel_name,
                }
            )

    async def webrtc_offer(self, event):
        if event['sender_channel_name'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer']
            }))

    async def webrtc_answer(self, event):
        if event['sender_channel_name'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer']
            }))

    async def webrtc_ice_candidate(self, event):
        if event['sender_channel_name'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate']
            }))

class WhiteboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'whiteboard_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send current whiteboard state to new user
        whiteboard_data = await self.get_whiteboard_data()
        if whiteboard_data:
            await self.send(text_data=json.dumps({
                'type': 'whiteboard_state',
                'data': whiteboard_data
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'draw':
            # Save to database
            await self.save_whiteboard_data(data['drawing_data'])

            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'whiteboard_draw',
                    'drawing_data': data['drawing_data'],
                    'sender_channel_name': self.channel_name,
                }
            )

    async def whiteboard_draw(self, event):
        if event['sender_channel_name'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'draw',
                'drawing_data': event['drawing_data']
            }))

    @database_sync_to_async
    def get_whiteboard_data(self):
        whiteboard = Whiteboard.objects.filter(chat_id=self.room_name).first()
        return whiteboard.data if whiteboard else None

    @database_sync_to_async
    def save_whiteboard_data(self, data):
        whiteboard, _ = Whiteboard.objects.get_or_create(chat_id=self.room_name)
        whiteboard.data = data
        whiteboard.save()

class PollConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'poll_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'create_poll':
            poll_id = await self.create_poll(data)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'poll_created',
                    'poll_id': poll_id,
                    'question': data['question'],
                    'options': data['options']
                }
            )
        elif data['type'] == 'vote':
            await self.save_vote(data)
            updated_results = await self.get_poll_results(data['poll_id'])
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'vote_updated',
                    'poll_id': data['poll_id'],
                    'results': updated_results
                }
            )

    async def poll_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'poll_created',
            'poll_id': event['poll_id'],
            'question': event['question'],
            'options': event['options']
        }))

    async def vote_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'vote_updated',
            'poll_id': event['poll_id'],
            'results': event['results']
        }))

    @database_sync_to_async
    def create_poll(self, data):
        poll = Poll.objects.create(
            chat_id=self.room_name,
            creator_id=self.scope['user'].id,
            question=data['question'],
            is_multiple_choice=data.get('is_multiple_choice', False)
        )
        for option_text in data['options']:
            PollOption.objects.create(poll=poll, text=option_text)
        return poll.id

    @database_sync_to_async
    def save_vote(self, data):
        PollVote.objects.create(
            poll_id=data['poll_id'],
            option_id=data['option_id'],
            user=self.scope['user']
        )

    @database_sync_to_async
    def get_poll_results(self, poll_id):
        poll = Poll.objects.get(id=poll_id)
        results = {}
        for option in poll.options.all():
            results[option.id] = option.pollvote_set.count()
        return results

class ScreenShareConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'screen_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_ended',
                'user_id': self.scope['user'].id
            }
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'start_sharing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'screen_share_started',
                    'user_id': self.scope['user'].id
                }
            )
        elif data['type'] == 'screen_data':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'screen_data',
                    'data': data['screen_data'],
                    'sender_channel_name': self.channel_name
                }
            )

    async def screen_share_started(self, event):
        await self.send(text_data=json.dumps({
            'type': 'screen_share_started',
            'user_id': event['user_id']
        }))

    async def screen_share_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'screen_share_ended',
            'user_id': event['user_id']
        }))

    async def screen_data(self, event):
        if event['sender_channel_name'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'screen_data',
                'data': event['screen_data']
            }))

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"video_call_{self.room_id}"

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Receive message from WebSocket
        data = json.loads(text_data)
        message = data['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_call_message',
                'message': message
            }
        )

    async def video_call_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))
