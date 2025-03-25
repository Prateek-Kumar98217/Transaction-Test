from django.urls import path
from .views import (
    AccountListCreate, AccountDetail,
    TransactionListCreate, TransactionView,
    UserRegisterView, UserDetailView,
    DepositView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    
    # Account endpoints
    path('accounts/', AccountListCreate.as_view(), name='account-list'),
    path('accounts/<int:pk>/', AccountDetail.as_view(), name='account-detail'),
    path('accounts/<int:pk>/deposit/', DepositView.as_view(), name='account-deposit'),
    
    # Transaction endpoints
    path('transactions/', TransactionListCreate.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', TransactionView.as_view(), name='transaction-detail'),
]
