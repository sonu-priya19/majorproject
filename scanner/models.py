# from django.db import models
# from django.contrib.auth.models import User

# class Feedback(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     message = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user.username} - {self.created_at}"
# from django.db import models
# from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.dispatch import receiver


# class Feedback(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     message = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
    
# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     age = models.PositiveIntegerField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.user.username} - {self.created_at}"
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # guard in case profile is missing for existing users
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.username} at {self.created_at:%Y-%m-%d %H:%M}"
    

class ScanHistory(models.Model):
    url = models.URLField(unique=True)
    result = models.CharField(max_length=20)  # "Phishing" or "Safe"
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    # ✅ new fields
    probability = models.FloatField(null=True, blank=True)   # 0.0 – 100.0
    features_json = models.JSONField(null=True, blank=True)  # saves dict of URL features

    def __str__(self):
        return f"{self.user.username} - {self.url} - {self.result}"
# class ScanHistory(models.Model):
#     url = models.URLField()
#     result = models.CharField(max_length=10, choices=[("safe", "Safe"), ("phishing", "Phishing")])
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     scanned_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.url} - {self.result}"


# class ScanHistory(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
#     url = models.URLField()
#     result = models.CharField(max_length=20)
#     reasons = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.url} - {self.result} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
