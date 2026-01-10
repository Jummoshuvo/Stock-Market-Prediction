from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Try to import bdshare and stocksurferbd
try:
    import bdshare as bd
    BD_SHARE_AVAILABLE = True
except ImportError:
    BD_SHARE_AVAILABLE = False
    logger.warning("bdshare library not available. Install it using: pip install bdshare")

try:
    from stocksurferbd import StockSurferBD
    STOCK_SURFER_AVAILABLE = True
except ImportError:
    STOCK_SURFER_AVAILABLE = False
    logger.warning("stocksurferbd library not available. Install it using: pip install stocksurferbd")


def get_stock_data_bdshare(symbol):
    """Fetch stock data using bdshare library"""
    try:
        if not BD_SHARE_AVAILABLE:
            return None
        
        # Get today's data
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # Fetch historical data - bdshare API: get_hist_data(start, end, code)
        df = bd.get_hist_data(start=start_date, end=end_date, code=symbol)
        
        if df is not None and not df.empty:
            return df
        return None
    except Exception as e:
        logger.error(f"Error fetching data from bdshare: {str(e)}")
        return None


def get_stock_data_stocksurfer(symbol):
    """Fetch stock data using stocksurferbd library"""
    try:
        if not STOCK_SURFER_AVAILABLE:
            return None

        # Use PriceData class from stocksurferbd
        price_data = PriceData()
        # Get historical data (last 60 days)
        data = price_data.get_hist_data(symbol, days=60)

        if data is not None and not data.empty:
            return data
        return None
    except Exception as e:
        logger.error(f"Error fetching data from stocksurferbd: {str(e)}")
        return None


def get_stock_data(symbol):
    """Try to get stock data from available sources"""
    # Try bdshare first
    data = get_stock_data_bdshare(symbol)
    if data is not None:
        return data, 'bdshare'
    
    # Try stocksurferbd
    data = get_stock_data_stocksurfer(symbol)
    if data is not None:
        return data, 'stocksurferbd'
    
    # Return None if both fail
    return None, None


def calculate_sma(data, window):
    """Calculate Simple Moving Average"""
    return data.rolling(window=window).mean()


def calculate_ema(data, window):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=window, adjust=False).mean()


def predict_price_simple_moving_average(df, days_ahead=30):
    """Simple prediction using moving averages"""
    if df is None or df.empty or len(df) < 10:
        return None
    
    # Use closing price
    if 'close' in df.columns:
        prices = df['close']
    elif 'Close' in df.columns:
        prices = df['Close']
    elif 'price' in df.columns:
        prices = df['price']
    else:
        prices = df.iloc[:, -1]  # Use last column as price
    
    # Calculate moving averages
    sma_5 = calculate_sma(prices, 5)
    sma_10 = calculate_sma(prices, 10)
    sma_20 = calculate_sma(prices, 20)
    
    # Get latest values
    latest_price = prices.iloc[-1]
    latest_sma_5 = sma_5.iloc[-1] if not pd.isna(sma_5.iloc[-1]) else latest_price
    latest_sma_10 = sma_10.iloc[-1] if not pd.isna(sma_10.iloc[-1]) else latest_price
    latest_sma_20 = sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else latest_price
    
    # Calculate trend
    trend = (latest_sma_5 + latest_sma_10 + latest_sma_20) / 3 - latest_price
    
    # Calculate volatility
    returns = prices.pct_change().dropna()
    volatility = returns.std() if len(returns) > 0 else 0.02
    
    # Predict future prices
    predictions = {}
    
    # Tomorrow (1 day)
    tomorrow_pred = latest_price + trend * 0.1 + np.random.normal(0, volatility * latest_price * 0.5)
    predictions['tomorrow'] = max(0, float(tomorrow_pred))
    
    # Next week (7 days)
    week_pred = latest_price + trend * 0.7 + np.random.normal(0, volatility * latest_price * 1.5)
    predictions['week'] = max(0, float(week_pred))
    
    # Next month (30 days)
    month_pred = latest_price + trend * 3 + np.random.normal(0, volatility * latest_price * 3)
    predictions['month'] = max(0, float(month_pred))
    
    # Calculate confidence based on data quality and volatility
    data_quality = min(100, len(df) * 2)  # More data = higher quality
    volatility_factor = max(0, 100 - (volatility * 1000))
    confidence = int((data_quality + volatility_factor) / 2)
    confidence = max(60, min(95, confidence))  # Clamp between 60-95%
    
    return {
        'predictions': predictions,
        'current_price': float(latest_price),
        'confidence': confidence,
        'volatility': float(volatility),
        'trend': 'up' if trend > 0 else 'down'
    }


def generate_historical_chart_data(df, current_price):
    """Generate historical data for chart"""
    if df is None or df.empty:
        return {'labels': [], 'data': []}

    # Get price column and convert to numeric
    if 'close' in df.columns:
        prices = pd.to_numeric(df['close'], errors='coerce')
    elif 'Close' in df.columns:
        prices = pd.to_numeric(df['Close'], errors='coerce')
    elif 'price' in df.columns:
        prices = pd.to_numeric(df['price'], errors='coerce')
    else:
        prices = pd.to_numeric(df.iloc[:, -1], errors='coerce')

    # Drop NaN values
    prices = prices.dropna()

    # Get last 30 days
    prices = prices.tail(30)

    if len(prices) == 0:
        return {'labels': [], 'data': []}

    # Generate labels
    labels = []
    for i in range(len(prices)):
        date = datetime.now() - timedelta(days=len(prices) - i - 1)
        labels.append(date.strftime('%b %d'))

    return {
        'labels': labels,
        'data': [float(p) for p in prices.values]
    }


@csrf_exempt
@require_http_methods(["POST", "GET"])
def predict_stock(request):
    """API endpoint for stock prediction"""
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            symbol = data.get('symbol', '').upper().strip()
        else:
            symbol = request.GET.get('symbol', '').upper().strip()
        
        if not symbol:
            return JsonResponse({
                'error': 'Stock symbol is required'
            }, status=400)
        
        # Fetch stock data
        df, source = get_stock_data(symbol)
        
        if df is None:
            # Return mock data if libraries are not available
            logger.warning(f"Stock data not available for {symbol}. Using mock data.")
            current_price = 100.0 + np.random.random() * 50
            predictions = {
                'tomorrow': current_price * (1 + np.random.normal(0, 0.02)),
                'week': current_price * (1 + np.random.normal(0, 0.05)),
                'month': current_price * (1 + np.random.normal(0, 0.1))
            }
            
            return JsonResponse({
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'predictions': {
                    'tomorrow': round(predictions['tomorrow'], 2),
                    'week': round(predictions['week'], 2),
                    'month': round(predictions['month'], 2)
                },
                'confidence': 75,
                'trend': 'up' if predictions['tomorrow'] > current_price else 'down',
                'historical_data': generate_historical_chart_data(None, current_price),
                'source': 'mock',
                'message': 'Using mock data. Please install bdshare or stocksurferbd for real data.'
            })
        
        # Generate prediction
        prediction_result = predict_price_simple_moving_average(df)
        
        if prediction_result is None:
            return JsonResponse({
                'error': 'Unable to generate prediction. Insufficient data.'
            }, status=400)
        
        # Generate historical chart data
        historical_data = generate_historical_chart_data(df, prediction_result['current_price'])
        
        return JsonResponse({
            'symbol': symbol,
            'current_price': prediction_result['current_price'],
            'predictions': {
                'tomorrow': round(prediction_result['predictions']['tomorrow'], 2),
                'week': round(prediction_result['predictions']['week'], 2),
                'month': round(prediction_result['predictions']['month'], 2)
            },
            'confidence': prediction_result['confidence'],
            'trend': prediction_result['trend'],
            'volatility': prediction_result['volatility'],
            'historical_data': historical_data,
            'source': source
        })
        
    except Exception as e:
        logger.error(f"Error in predict_stock: {str(e)}")
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_stock_list(request):
    """Get list of available Bangladeshi stocks"""
    # Common Bangladeshi stock symbols
    bangladeshi_stocks = [
        {'symbol': 'GP', 'name': 'Grameenphone Ltd'},
        {'symbol': 'SQUARE', 'name': 'Square Pharmaceuticals Ltd'},
        {'symbol': 'BEXIMCO', 'name': 'Beximco Pharmaceuticals Ltd'},
        {'symbol': 'RENATA', 'name': 'Renata Limited'},
        {'symbol': 'ACI', 'name': 'ACI Limited'},
        {'symbol': 'BRACBANK', 'name': 'BRAC Bank Limited'},
        {'symbol': 'EBL', 'name': 'Eastern Bank Limited'},
        {'symbol': 'DUTCHBANGLA', 'name': 'Dutch-Bangla Bank Limited'},
        {'symbol': 'BANKASIA', 'name': 'Bank Asia Limited'},
        {'symbol': 'IFIC', 'name': 'IFIC Bank Limited'},
    ]
    
    return JsonResponse({
        'stocks': bangladeshi_stocks,
        'total': len(bangladeshi_stocks)
    })


def news_detail(request, slug):
    """Display news article detail page"""
    from django.shortcuts import render
    
    # News articles data
    news_articles = {
        'market-updates': {
            'title': 'Bangladesh Stock Market Shows Strong Growth in Q4 2024',
            'category': 'Market Updates',
            'category_bg': 'bg-blue-100',
            'category_text': 'text-blue-700',
            'icon': 'fas fa-chart-line',
            'icon_bg': 'bg-blue-100',
            'icon_color': 'text-blue-600',
            'date': 'January 15, 2025',
            'author': 'Stock Market Analyst',
            'read_time': '5',
            'image': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800',
            'content': '''
                <p class="text-lg text-gray-700 mb-6 leading-relaxed">
                    The Bangladesh stock market has demonstrated remarkable resilience and growth in the fourth quarter of 2024, 
                    with the DSEX index reaching new heights. This positive trend reflects strong investor confidence and 
                    improving economic fundamentals.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">Key Market Highlights</h2>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>DSEX index closed at 6,234.56 points, up 12.5% from the previous quarter</li>
                    <li>Total market capitalization increased to ৳4.5 trillion</li>
                    <li>Average daily turnover reached ৳850 crore</li>
                    <li>Foreign investment inflow increased by 35%</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">Sector Performance</h2>
                <p class="text-gray-700 mb-4">
                    The banking sector led the gains with a 15% increase, followed by pharmaceuticals (12%) and telecommunications (10%). 
                    The textile sector also showed strong performance, contributing significantly to the overall market growth.
                </p>
                
                <div class="bg-indigo-50 border-l-4 border-indigo-500 p-4 my-6">
                    <p class="text-gray-700 italic">
                        "The market's strong performance reflects growing investor confidence in Bangladesh's economic prospects. 
                        We expect this positive trend to continue into 2025." - Market Analyst
                    </p>
                </div>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">Outlook for 2025</h2>
                <p class="text-gray-700 mb-4">
                    Analysts remain optimistic about the market's prospects for 2025. Key factors supporting this outlook include:
                </p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Stable economic growth projections</li>
                    <li>Improved corporate earnings</li>
                    <li>Favorable government policies</li>
                    <li>Increasing foreign direct investment</li>
                </ul>
                
                <p class="text-gray-700 mt-6">
                    Investors are advised to maintain a diversified portfolio and stay informed about market developments. 
                    Regular monitoring of company fundamentals and market trends is essential for successful investing.
                </p>
            '''
        },
        'company-news': {
            'title': 'Major Bangladeshi Companies Announce Q4 Earnings',
            'category': 'Company News',
            'category_bg': 'bg-purple-100',
            'category_text': 'text-purple-700',
            'icon': 'fas fa-bullhorn',
            'icon_bg': 'bg-purple-100',
            'icon_color': 'text-purple-600',
            'date': 'January 12, 2025',
            'author': 'Business Reporter',
            'read_time': '6',
            'image': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800',
            'content': '''
                <p class="text-lg text-gray-700 mb-6 leading-relaxed">
                    Several leading Bangladeshi companies have released their fourth quarter earnings reports, 
                    showing mixed results across different sectors. The announcements have generated significant 
                    interest among investors and market analysts.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">Grameenphone (GP) Performance</h2>
                <p class="text-gray-700 mb-4">
                    Grameenphone reported strong quarterly earnings with revenue growth of 8.5% year-over-year. 
                    The company's subscriber base continued to expand, reaching 85 million active users. 
                    The stock price responded positively, closing at ৳245.50.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">Square Pharmaceuticals Results</h2>
                <p class="text-gray-700 mb-4">
                    Square Pharmaceuticals announced steady growth in both domestic and international markets. 
                    The company's export revenue increased by 12%, while domestic sales grew by 6%. 
                    Strong performance in the pharmaceutical sector continues to drive investor interest.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">Banking Sector Updates</h2>
                <p class="text-gray-700 mb-4">
                    Major banks including BRAC Bank, Eastern Bank, and Dutch-Bangla Bank reported improved 
                    net interest margins and asset quality. The banking sector's overall performance has been 
                    positive, with non-performing loans showing a declining trend.
                </p>
                
                <div class="bg-purple-50 border-l-4 border-purple-500 p-4 my-6">
                    <p class="text-gray-700 italic">
                        "The earnings season has been largely positive, with most companies meeting or exceeding 
                        expectations. This bodes well for the market's continued growth." - Financial Analyst
                    </p>
                </div>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">Key Announcements</h2>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Beximco Pharmaceuticals announced expansion plans for new manufacturing facilities</li>
                    <li>ACI Limited reported record quarterly sales in consumer goods division</li>
                    <li>Renata Limited declared dividend of ৳5 per share</li>
                    <li>Several banks announced plans for digital banking initiatives</li>
                </ul>
                
                <p class="text-gray-700 mt-6">
                    Investors should carefully review individual company earnings reports and consider the 
                    long-term growth prospects before making investment decisions.
                </p>
            '''
        },
        'investment-tips': {
            'title': 'Expert Investment Tips for Bangladeshi Stock Market in 2025',
            'category': 'Investment Tips',
            'category_bg': 'bg-green-100',
            'category_text': 'text-green-700',
            'icon': 'fas fa-trending-up',
            'icon_bg': 'bg-green-100',
            'icon_color': 'text-green-600',
            'date': 'January 10, 2025',
            'author': 'Investment Advisor',
            'read_time': '7',
            'image': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800',
            'content': '''
                <p class="text-lg text-gray-700 mb-6 leading-relaxed">
                    Investing in the Bangladeshi stock market requires careful planning, research, and a 
                    disciplined approach. Here are expert tips to help you navigate the market successfully in 2025.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">1. Diversify Your Portfolio</h2>
                <p class="text-gray-700 mb-4">
                    Don't put all your eggs in one basket. Spread your investments across different sectors 
                    such as banking, pharmaceuticals, telecommunications, and manufacturing. This helps 
                    reduce risk and provides better returns over the long term.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">2. Research Before Investing</h2>
                <p class="text-gray-700 mb-4">
                    Always research companies before investing. Look at their financial statements, 
                    earnings history, management quality, and growth prospects. Understanding the 
                    fundamentals is crucial for making informed decisions.
                </p>
                
                <div class="bg-green-50 border-l-4 border-green-500 p-4 my-6">
                    <p class="text-gray-700 italic">
                        "Successful investing is about time in the market, not timing the market. 
                        Focus on quality companies with strong fundamentals." - Investment Expert
                    </p>
                </div>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">3. Invest for the Long Term</h2>
                <p class="text-gray-700 mb-4">
                    Stock market investing should be viewed as a long-term wealth-building strategy. 
                    Short-term market fluctuations are normal, but quality stocks tend to appreciate 
                    over time. Avoid panic selling during market downturns.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">4. Monitor Market Trends</h2>
                <p class="text-gray-700 mb-4">
                    Stay informed about market trends, economic indicators, and company news. 
                    Regular monitoring helps you make timely decisions and adjust your portfolio as needed.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">5. Set Realistic Expectations</h2>
                <p class="text-gray-700 mb-4">
                    Don't expect to get rich quick. Set realistic return expectations and invest 
                    only what you can afford to lose. The stock market involves risk, and it's 
                    important to be prepared for both gains and losses.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">6. Consider Dividend Stocks</h2>
                <p class="text-gray-700 mb-4">
                    Dividend-paying stocks can provide a steady income stream. Many Bangladeshi 
                    companies, especially in the banking and pharmaceutical sectors, offer regular 
                    dividends. This can be particularly attractive for income-focused investors.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">7. Use Stop-Loss Orders</h2>
                <p class="text-gray-700 mb-4">
                    Consider using stop-loss orders to limit potential losses. This helps protect 
                    your capital and ensures you don't hold onto losing positions for too long.
                </p>
                
                <h2 class="text-2xl font-bold text-gray-800 mt-8 mb-4">8. Seek Professional Advice</h2>
                <p class="text-gray-700 mb-4">
                    If you're new to investing, consider consulting with a financial advisor. 
                    Professional guidance can help you develop a sound investment strategy tailored 
                    to your financial goals and risk tolerance.
                </p>
                
                <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 my-6">
                    <p class="text-gray-700 font-semibold">
                        <i class="fas fa-exclamation-triangle mr-2"></i>Important Disclaimer:
                    </p>
                    <p class="text-gray-700 mt-2">
                        All investments carry risk. Past performance does not guarantee future results. 
                        Always do your own research and consider your financial situation before investing. 
                        This information is for educational purposes only and should not be considered 
                        as financial advice.
                    </p>
                </div>
            '''
        }
    }
    
    # Get the article or return 404
    article = news_articles.get(slug)
    if not article:
        from django.http import Http404
        raise Http404("News article not found")
    
    # Get related news (exclude current article)
    related_news = [
        {'slug': 'market-updates', 'title': 'Market Updates', 'excerpt': 'Latest market trends and analysis'},
        {'slug': 'company-news', 'title': 'Company News', 'excerpt': 'Latest company announcements'},
        {'slug': 'investment-tips', 'title': 'Investment Tips', 'excerpt': 'Expert investment advice'}
    ]
    related_news = [news for news in related_news if news['slug'] != slug]
    
    context = {
        'news_title': article['title'],
        'news_category': article['category'],
        'news_category_bg': article['category_bg'],
        'news_category_text': article['category_text'],
        'news_icon': article['icon'],
        'news_icon_bg': article['icon_bg'],
        'news_icon_color': article['icon_color'],
        'news_date': article['date'],
        'news_author': article['author'],
        'news_read_time': article['read_time'],
        'news_image': article.get('image', ''),
        'news_content': article['content'],
        'related_news': related_news
    }
    
    return render(request, 'news_detail.html', context)


def signup_view(request):
    """User sign up page"""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        errors = []
        if not username:
            errors.append('Username is required')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        
        if not email:
            errors.append('Email is required')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered')
        
        if not phone_number:
            errors.append('Phone number is required')
        
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        elif password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            return render(request, 'signup.html', {
                'errors': errors,
                'username': username,
                'email': email,
                'phone_number': phone_number
            })
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            # Update profile with phone number
            if hasattr(user, 'profile'):
                user.profile.phone_number = phone_number
                user.profile.save()
            else:
                UserProfile.objects.create(user=user, phone_number=phone_number)
            
            # Auto login
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to StockPredictor!')
            # Redirect to 'next' URL if provided, otherwise home
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return render(request, 'signup.html', {
                'errors': ['An error occurred. Please try again.'],
                'username': username,
                'email': email,
                'phone_number': phone_number
            })
    
    return render(request, 'signup.html')


def login_view(request):
    """User login page"""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            return render(request, 'login.html', {
                'error': 'Please enter both username and password'
            })
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password'
            })
    
    return render(request, 'login.html')


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/')


def trading_view(request):
    """Trading platform - requires authentication"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign up or login first to access the trading platform.')
        return redirect('/login/?next=/trading/')
    return render(request, 'trading.html')


@csrf_exempt
@require_http_methods(["GET", "POST"])
def trading_data(request):
    """Get or update trading data (balance, portfolio, orders)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    from .models import TradingAccount, StockOrder, Portfolio
    
    if request.method == 'GET':
        try:
            # Get user's trading data
            account = TradingAccount.get_or_create_account(request.user)
            orders = StockOrder.objects.filter(user=request.user).order_by('-timestamp')[:10]  # Last 10 orders
            portfolio_items = Portfolio.objects.filter(user=request.user).order_by('-updated_at')[:10]  # Last 10 portfolio items
            
            # Log for debugging
            logger.info(f"Loading trading data for user {request.user.username}: {orders.count()} orders, {portfolio_items.count()} portfolio items")
            
            orders_list = [{
                'id': order.id,
                'symbol': order.symbol,
                'type': order.order_type,
                'quantity': order.quantity,
                'price': float(order.price),
                'total': float(order.total_amount),
                'timestamp': order.timestamp.isoformat()
            } for order in orders]
            
            return JsonResponse({
                'success': True,
                'balance': float(account.balance),
                'orders': orders_list,
                'portfolio': [{
                    'symbol': item.symbol,
                    'quantity': item.quantity,
                    'avg_price': float(item.avg_price)
                } for item in portfolio_items]
            })
        except Exception as e:
            logger.error(f"Error in trading_data GET: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
    
    elif request.method == 'POST':
        # Save new order and update balance/portfolio
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol', '').upper()
            order_type = data.get('type', '').upper()  # BUY or SELL
            quantity = int(data.get('quantity', 0))
            price = Decimal(str(data.get('price', 0)))
            total = quantity * price
            
            if not symbol or order_type not in ['BUY', 'SELL'] or quantity <= 0 or price <= 0:
                return JsonResponse({'error': 'Invalid order data'}, status=400)
            
            account = TradingAccount.get_or_create_account(request.user)
            
            if order_type == 'BUY':
                if total > account.balance:
                    return JsonResponse({'error': 'Insufficient balance'}, status=400)
                account.balance -= Decimal(str(total))
                
                # Update or create portfolio
                portfolio_item, created = Portfolio.objects.get_or_create(
                    user=request.user,
                    symbol=symbol,
                    defaults={'quantity': quantity, 'avg_price': Decimal(str(price))}
                )
                if not created:
                    # Calculate new average price
                    old_total = portfolio_item.quantity * portfolio_item.avg_price
                    new_total = old_total + total
                    portfolio_item.quantity += quantity
                    portfolio_item.avg_price = Decimal(str(new_total / portfolio_item.quantity))
                    portfolio_item.save()
            else:  # SELL
                try:
                    portfolio_item = Portfolio.objects.get(user=request.user, symbol=symbol)
                    if portfolio_item.quantity < quantity:
                        return JsonResponse({'error': 'Insufficient shares to sell'}, status=400)
                    
                    account.balance += Decimal(str(total))
                    portfolio_item.quantity -= quantity
                    if portfolio_item.quantity <= 0:
                        portfolio_item.delete()
                    else:
                        portfolio_item.save()
                except Portfolio.DoesNotExist:
                    return JsonResponse({'error': 'You don\'t own this stock'}, status=400)
            
            account.save()
            
            # Create order record
            order = StockOrder.objects.create(
                user=request.user,
                symbol=symbol,
                order_type=order_type,
                quantity=quantity,
                price=Decimal(str(price)),
                total_amount=Decimal(str(total))
            )
            
            return JsonResponse({
                'success': True,
                'balance': float(account.balance),
                'order_id': order.id
            })
            
        except Exception as e:
            logger.error(f"Error processing trade: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def contact_form(request):
    """Handle contact form submission and send email"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        # Validation
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Name is required'
            }, status=400)
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email is required'
            }, status=400)
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Message is required'
            }, status=400)
        
        # Email subject and body
        subject = f'Contact Form Submission from {name} - StockPredictor'
        email_body = f"""
You have received a new contact form submission from StockPredictor website.

Name: {name}
Email: {email}

Message:
{message}

---
This email was sent from the StockPredictor contact form.
        """
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            
            # Send confirmation email to user
            confirmation_subject = 'Thank you for contacting StockPredictor'
            confirmation_body = f"""
Dear {name},

Thank you for contacting StockPredictor. We have received your message and will get back to you soon.

Your message:
{message}

Best regards,
StockPredictor Team
            """
            
            send_mail(
                subject=confirmation_subject,
                message=confirmation_body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=True,  # Don't fail if user email is invalid
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Your message has been sent successfully! We will get back to you soon.'
            })
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to send email: {str(e)}'
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in contact_form: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)

