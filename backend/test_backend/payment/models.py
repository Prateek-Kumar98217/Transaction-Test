from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
# Create your models here.

class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pin = models.CharField(unique=True, max_length=255)  
    balance = models.DecimalField(max_digits=10, decimal_places=2,  default=0)

    def save(self, *args, **kwargs):
        if self.pin and not self.pin.startswith('pbkdf2_sha256'): 
            self.pin = make_password(self.pin)
        super().save(*args, **kwargs)

    def set_pin(self, pin):
        self.pin = pin
        self.save()

    def check_pin(self, pin):
        result = check_password(pin, self.pin)
        print("Check result:", result)
        return result

    def __str__(self):
        return self.user.username

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    sender_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sender')
    receiver_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='receiver')
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='Pending')

    def __str__(self):
        return f'{self.sender_account.user.username} -> {self.receiver_account.user.username} : {self.amount}'