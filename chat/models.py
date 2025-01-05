from django.db import models

class ChatMessage(models.Model):
    sender = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="uploads/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} at {self.timestamp}: {self.message or 'File'}"
