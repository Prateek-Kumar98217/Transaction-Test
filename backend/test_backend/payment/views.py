from django.db import transaction
from django.db.models import Q
from .models import Account, Transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import (
    AccountSerializer, TransactionSerializer, UserSerializer,
    DepositSerializer
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsOwner
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
# Create your views here.

class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "data": UserSerializer(user).data,
                "message": "User registered successfully"
            }, status=status.HTTP_201_CREATED)
        return Response({
            "errors": serializer.errors,
            "message": "Registration failed"
        }, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "User details retrieved successfully"
        })

class AccountListCreate(generics.ListCreateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self): 
        return Account.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Accounts retrieved successfully"
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save(user=self.request.user)
            return Response({
                "data": AccountSerializer(account).data,
                "message": "Account created successfully"
            }, status=status.HTTP_201_CREATED)
        return Response({
            "errors": serializer.errors,
            "message": "Account creation failed"
        }, status=status.HTTP_400_BAD_REQUEST)

class AccountDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Account details retrieved successfully"
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            account = serializer.save()
            return Response({
                "data": AccountSerializer(account).data,
                "message": "Account updated successfully"
            })
        return Response({
            "errors": serializer.errors,
            "message": "Account update failed"
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Account deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)

class TransactionListCreate(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(
            Q(sender_account__user=user) | Q(receiver_account__user=user)
        ).select_related('sender_account', 'receiver_account')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Transactions retrieved successfully"
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                try:
                    sender_account = serializer.validated_data.get('sender_account')
                    receiver_account = serializer.validated_data.get('receiver_account')
                    amount = serializer.validated_data.get('amount')
                    
                    # Validate accounts exist and belong to user
                    if not sender_account or not receiver_account:
                        return Response({
                            "message": "Invalid sender or receiver account"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check sufficient balance
                    if sender_account.balance < amount:
                        return Response({
                            "message": "Insufficient balance"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check minimum transaction amount
                    if amount < 0.01:
                        return Response({
                            "message": "Transaction amount must be at least 0.01"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check maximum transaction amount (e.g., 10000)
                    if amount > 10000:
                        return Response({
                            "message": "Transaction amount exceeds maximum limit"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    sender_account.balance -= amount
                    receiver_account.balance += amount
                    sender_account.save()
                    receiver_account.save()
                    
                    transaction_obj = serializer.save(status='Success')
                    return Response({
                        "data": TransactionSerializer(transaction_obj).data,
                        "message": "Transaction completed successfully"
                    }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({
                        "message": f"Transaction failed: {str(e)}"
                    }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "errors": serializer.errors,
            "message": "Transaction validation failed"
        }, status=status.HTTP_400_BAD_REQUEST)

class TransactionView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(
            Q(sender_account__user=user) | Q(receiver_account__user=user)
        ).select_related('sender_account', 'receiver_account')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Transaction details retrieved successfully"
        })

class DepositView(generics.GenericAPIView):
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        account_id = self.kwargs.get('pk')
        return Account.objects.get(account_id=account_id, user=self.request.user)

    def post(self, request, *args, **kwargs):
        account = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'account': account})
        
        if serializer.is_valid():
            with transaction.atomic():
                try:
                    amount = serializer.validated_data['amount']
                    account.balance += amount
                    account.save()
                    
                    # Create transaction record
                    Transaction.objects.create(
                        sender_account=account,
                        receiver_account=account,  # Same account for deposits
                        amount=amount,
                        status='Cash Deposit'
                    )
                    
                    return Response({
                        "data": {
                            "account_id": account.account_id,
                            "new_balance": account.balance,
                            "amount_deposited": amount
                        },
                        "message": "Deposit successful"
                    })
                except Exception as e:
                    return Response({
                        "message": f"Deposit failed: {str(e)}"
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "errors": serializer.errors,
            "message": "Deposit validation failed"
        }, status=status.HTTP_400_BAD_REQUEST)