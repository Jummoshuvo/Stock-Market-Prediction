"""
Quick script to check if orders are being saved in the database.
Run this from the Django shell or as a management command.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockpredictor.settings')
django.setup()

from django.contrib.auth.models import User
from predictor.models import StockOrder, TradingAccount, Portfolio

# Get all users
users = User.objects.all()
print(f"Total users: {users.count()}\n")

for user in users:
    print(f"User: {user.username}")
    print(f"  - Trading Account Balance: ৳{TradingAccount.get_or_create_account(user).balance}")
    print(f"  - Total Orders: {StockOrder.objects.filter(user=user).count()}")
    print(f"  - Portfolio Items: {Portfolio.objects.filter(user=user).count()}")
    
    # Show recent orders
    recent_orders = StockOrder.objects.filter(user=user).order_by('-timestamp')[:5]
    if recent_orders.exists():
        print("  - Recent Orders:")
        for order in recent_orders:
            print(f"    * {order.order_type} {order.quantity} {order.symbol} @ ৳{order.price} on {order.timestamp}")
    else:
        print("  - No orders found")
    print()

