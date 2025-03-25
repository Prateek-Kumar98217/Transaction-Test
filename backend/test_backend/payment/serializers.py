from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Account, Transaction

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'id': {'read_only': True},
            'email': {'required': True},
            'password': {'required': True, 'write_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password
        )
        return user

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['account_id', 'user', 'pin', 'balance']

        extra_kwargs = {
            'account_id': {'read_only': True},
            'user': {'read_only': True},
            'pin': {'write_only': True},
            'balance': {'read_only': True},
        }

    def validate_pin(self, value):
        if not value.isdigit() or len(value) != 4:
            raise serializers.ValidationError("PIN must be exactly 4 digits")
        return value

    def create(self, validated_data):
        pin = validated_data.pop('pin')
        account = Account(**validated_data)
        account.set_pin(pin)
        account.save()
        return account

    def update(self, instance, validated_data):
        pin = validated_data.pop('pin', None)
        if pin:
            instance.set_pin(pin)
        return super().update(instance, validated_data)

class TransactionSerializer(serializers.ModelSerializer):
    pin = serializers.CharField(write_only=True)
    class Meta:
        model = Transaction
        fields = ['transaction_id', 'sender_account', 'receiver_account', 'amount', 'date', 'status', 'pin']

        extra_kwargs = {
            'transaction_id': {'read_only': True},
            'date': {'read_only': True},
            'status': {'read_only': True},
            'pin': {'write_only': True},
        }

    def create(self, validated_data):
        # Remove pin from validated_data as it's not a field in Transaction model
        validated_data.pop('pin', None)
        return super().create(validated_data)

    def validate(self, data):
        sender_account = data['sender_account']
        print(sender_account)
        receiver_account = data['receiver_account']
        print(receiver_account)
        pin = data['pin']
        amount = data['amount']
        if sender_account.balance < amount:
            raise serializers.ValidationError('Insufficient balance')
        if sender_account == receiver_account:
            raise serializers.ValidationError('Cannot transfer to the same account')
        if not Account.objects.filter(account_id=receiver_account.account_id).exists():
            raise serializers.ValidationError('Receiver account does not exist')
        if not sender_account.check_pin(pin):
            raise serializers.ValidationError('Invalid pin')
        return data

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    pin = serializers.CharField(write_only=True)

    def validate(self, data):
        account = self.context['account']
        pin = data['pin']
        if not account.check_pin(pin):
            raise serializers.ValidationError('Invalid PIN')
        return data