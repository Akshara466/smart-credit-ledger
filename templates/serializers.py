
from rest_framework import serializers
from datetime import datetime


class TransactionSerializer(serializers.Serializer):

    accountNumber = serializers.CharField(
        max_length=50,
        allow_blank=False
    )

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    transactionType = serializers.CharField(
        max_length=20,
        allow_blank=False
    )

    time = serializers.CharField()

    def validate_time(self, value):
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise serializers.ValidationError(
                "Invalid date/time format. Use ISO format."
            )

        return value
