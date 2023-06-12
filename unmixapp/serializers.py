from rest_framework import serializers
from .models import *


class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ['upload_path', 'result_path', 'instrument', ]
