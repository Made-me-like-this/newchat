# Generated by Django 5.0.1 on 2025-01-31 09:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_userprofile_friends'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='code_language',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='edited_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='chat_files/'),
        ),
        migrations.AddField(
            model_name='message',
            name='file_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='message_type',
            field=models.CharField(choices=[('text', 'Text Message'), ('file', 'File Share'), ('system', 'System Message'), ('code', 'Code Block'), ('poll', 'Poll')], default='text', max_length=10),
        ),
        migrations.AddField(
            model_name='message',
            name='parent_message',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='chat.message'),
        ),
        migrations.AddField(
            model_name='room',
            name='allow_file_sharing',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='room',
            name='allow_screen_sharing',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='room',
            name='allow_video_calls',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='room',
            name='allow_voice_calls',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='room',
            name='categories',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='room',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='room',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='room',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='room',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ends_at', models.DateTimeField(blank=True, null=True)),
                ('is_multiple_choice', models.BooleanField(default=False)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.room')),
            ],
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='chat.poll')),
            ],
        ),
        migrations.CreateModel(
            name='PollVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.polloption')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.poll')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PrivateChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_message_at', models.DateTimeField(auto_now=True)),
                ('participants', models.ManyToManyField(related_name='private_chats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_message_at'],
            },
        ),
        migrations.AddField(
            model_name='poll',
            name='private_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.privatechat'),
        ),
        migrations.CreateModel(
            name='PrivateMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('file', models.FileField(blank=True, null=True, upload_to='private_messages/')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.privatechat')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_private_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='RoomInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending', max_length=10)),
                ('invited_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invitations', to=settings.AUTH_USER_MODEL)),
                ('invited_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_invitations', to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.room')),
            ],
        ),
        migrations.CreateModel(
            name='VoiceCall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('ongoing', 'Ongoing'), ('ended', 'Ended'), ('missed', 'Missed')], max_length=20)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.privatechat')),
                ('started_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Whiteboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('data', models.JSONField(default=dict)),
                ('private_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.privatechat')),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.room')),
            ],
        ),
        migrations.CreateModel(
            name='MessageReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reaction_type', models.CharField(choices=[('like', '👍'), ('love', '❤️'), ('laugh', '😄'), ('sad', '😢'), ('angry', '😠'), ('wow', '😮')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='chat.message')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('message', 'user', 'reaction_type')},
            },
        ),
    ]
