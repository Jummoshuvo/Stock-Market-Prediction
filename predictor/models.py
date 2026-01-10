from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class UserProfile(models.Model):
    """Extended user profile with phone number"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile when user is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class TradingAccount(models.Model):
    """User's trading account with balance"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trading_account')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Balance: ৳{self.balance}"
    
    @classmethod
    def get_or_create_account(cls, user):
        """Get or create trading account for user"""
        account, created = cls.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100000.00')}
        )
        return account


class StockOrder(models.Model):
    """Stock trading orders"""
    ORDER_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    symbol = models.CharField(max_length=20)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPES)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.order_type} {self.quantity} {self.symbol} @ ৳{self.price}"


class Portfolio(models.Model):
    """User's stock portfolio holdings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_items')
    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField()
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'symbol']
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.user.username} - {self.symbol}: {self.quantity} @ ৳{self.avg_price}"

