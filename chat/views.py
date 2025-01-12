from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Chat, Message, User
import json
from .forms import UserProfileForm, CustomUserCreationForm
from .models import ChatMessage
from .forms import MessageForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat:chat_list')  
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'chat:chat_list')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('chat:chat_list')  
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chat:chat_list')  
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('chat:profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'auth/profile.html', {'form': form})

@login_required
def chat_list(request):
    chats = Chat.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__timestamp')
    ).prefetch_related(
        'participants',
        Prefetch(
            'messages',
            queryset=Message.objects.order_by('-timestamp')[:1],
            to_attr='latest_message'
        )
    ).order_by('-last_message_time')

    for chat in chats:
        chat.unread_count = chat.messages.filter(
            read=False
        ).exclude(
            sender=request.user
        ).count()

    return render(request, 'chat/chat_list.html', {'chats': chats})

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    
    Message.objects.filter(
        chat=chat, read=False
    ).exclude(sender=request.user).update(read=True)
    
    messages = chat.messages.select_related('sender').order_by('-timestamp')
    paginator = Paginator(messages, 50)
    page = request.GET.get('page')
    messages = paginator.get_page(page)
    
    other_participants = chat.participants.exclude(id=request.user.id)
    
    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages': messages,
        'other_participants': other_participants,
    })

@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        chat_id = data.get('chat_id')
        message_content = data.get('message')
        
        if not chat_id or not message_content:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)
        
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        message = Message.objects.create(chat=chat, sender=request.user, content=message_content)
        
        chat.last_activity = timezone.now()
        chat.save()
        
        return JsonResponse({
            'status': 'success',
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'sender_name': message.sender.get_full_name(),
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def create_chat(request):
    if request.method == 'POST':
        participant_id = request.POST.get('participants')
        
        if not participant_id:
            messages.error(request, 'Please select a participant')
            return redirect('chat:create_chat')
        
        existing_chat = Chat.objects.filter(
            participants=request.user
        ).filter(
            participants=participant_id
        ).first()
        
        if existing_chat:
            return redirect('chat:chat_detail', chat_id=existing_chat.id)
            
        chat = Chat.objects.create()
        participant = User.objects.get(id=participant_id)
        chat.participants.add(request.user, participant)
        
        return redirect('chat:chat_detail', chat_id=chat.id)
    
    available_users = User.objects.exclude(id=request.user.id).order_by('first_name')
    return render(request, 'chat/create_chat.html', {'available_users': available_users})

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    
    # Mark messages as read
    Message.objects.filter(
        chat=chat, 
        read=False
    ).exclude(
        sender=request.user
    ).update(read=True)
    
    # Get all messages for this chat
    messages = chat.messages.select_related('sender').order_by('timestamp')
    other_participant = chat.participants.exclude(id=request.user.id).first()
    
    context = {
        'chat': chat,
        'messages': messages,
        'other_participant': other_participant,
    }
    
    return render(request, 'chat/chat_detail.html', context)

@login_required
def chat_area(request):
    form = MessageForm()
    messages = ChatMessage.objects.all()
    return render(request, 'chat/chat_area.html', {
        'form': form,
        'messages': messages
    })

@login_required
def load_more_messages(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    last_message_id = request.GET.get('last_message_id')
    
    if not last_message_id:
        return JsonResponse({'status': 'error', 'message': 'No last message ID provided'}, status=400)
    
    messages = chat.messages.filter(id__lt=last_message_id).select_related('sender').order_by('-timestamp')[:20]
    messages_data = [
        {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'sender_name': message.sender.get_full_name(),
        }
        for message in messages
    ]
    return JsonResponse({'status': 'success', 'messages': messages_data})

def logout(request):
    return render(request, 'chat:login')