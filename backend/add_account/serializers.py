from rest_framework import serializers

class AddAccountDetailsSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=50)
    account_holder_name = serializers.CharField(max_length=100)
    bank_name = serializers.CharField(max_length=100)
    branch_name = serializers.CharField(max_length=100)
    ifsc_code = serializers.CharField(max_length=20)
    unique_code = serializers.CharField(max_length=6)  # New field for unique code
    pin_no = serializers.RegexField(
        regex=r'^\d{4}$',
        max_length=4,
        error_messages={'invalid': 'PIN must be exactly 4 digits.'}
    )

class VerifyPinSerializer(serializers.Serializer):
    pin = serializers.RegexField(
        regex=r'^\d{4}$',
        max_length=4,
        error_messages={'invalid': 'PIN must be exactly 4 digits.'}
    )
