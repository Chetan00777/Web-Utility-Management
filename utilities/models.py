from django.db import models
from django.contrib.auth.models import User

class Utility(models.Model):
    UTILITY_TYPES = [
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
        ('steam', 'Steam'),
        ('air_conditioning', 'Air Conditioning'),
    ]

    type = models.CharField(max_length=20, choices=UTILITY_TYPES)
    usage = models.FloatField()
    date = models.DateTimeField()
    notes = models.TextField(blank=True)
    file_s3_key = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.usage}"
