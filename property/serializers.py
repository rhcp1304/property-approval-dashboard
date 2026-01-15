from rest_framework import serializers
from .models import PropertyRecord

class PropertyRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyRecord
        fields = '__all__' # Sends all fields including financial and resource links