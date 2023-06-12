import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from .managers import CustomUserManager

STATUS_LIST = (
    ("PEN", "pending"),
    ("PROCESS", "processing"),
    ("DONE", "done"),
)


class User(AbstractUser):
    object = CustomUserManager()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{11}$',
                                 message="Не корректный формат номера телефона")

    username = None
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', ]

    def save(self, *args, **kwargs):
        super().save()

    def __str__(self) -> str:
        return f"{self.pk} - {self.email}"


class Track(models.Model):
    upload_path = models.CharField(max_length=200, null=True, blank=True)
    result_path = models.CharField(max_length=200, null=True, blank=True)
    instrument = models.CharField(max_length=200, unique=False)
    status = models.CharField(max_length=20, choices=STATUS_LIST, default="PEN")
    user_id = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.upload_path is not None:
            return f"{self.instrument}_{self.upload_path.split('/')[-1].split('.')[0]}"

        else:
            return f"{self.id} unprocessed"

    def has_feedback(self):
        return Feedback.objects.filter(track_id=self).exists()

    def get_original_filename(self):
        return os.path.basename(self.upload_path)


class Feedback(models.Model):
    text = models.TextField(max_length=500, null=True, blank=True)
    score = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    user_id = models.ForeignKey(to=User, on_delete=models.CASCADE)
    track_id = models.ForeignKey(to=Track, on_delete=models.CASCADE)
