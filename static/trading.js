// Trading Platform JavaScript

// Bangladeshi Stock Market Data
const bangladeshiStocks = [
    { symbol: 'GP', name: 'Grameenphone Ltd', price: 245.50, change: 2.35, volume: 1250000 },
    { symbol: 'SQUARE', name: 'Square Pharmaceuticals', price: 189.75, change: -1.20, volume: 890000 },
    { symbol: 'BEXIMCO', name: 'Beximco Pharmaceuticals', price: 156.30, change: 3.45, volume: 2100000 },
    { symbol: 'RENATA', name: 'Renata Limited', price: 278.90, change: 0.85, volume: 450000 },
    { symbol: 'ACI', name: 'ACI Limited', price: 198.40, change: -0.65, volume: 320000 },
    { symbol: 'BRACBANK', name: 'BRAC Bank Limited', price: 45.60, change: 1.25, volume: 1800000 },
    { symbol: 'EBL', name: 'Eastern Bank Limited', price: 38.25, change: -0.45, volume: 950000 },
    { symbol: 'DUTCHBANGLA', name: 'Dutch-Bangla Bank', price: 42.80, change: 2.10, volume: 1100000 },
    { symbol: 'BANKASIA', name: 'Bank Asia Limited', price: 22.15, change: 0.35, volume: 750000 },
    { symbol: 'IFIC', name: 'IFIC Bank Limited', price: 18.90, change: -0.80, volume: 650000 },
    { symbol: 'ISLAMI', name: 'Islami Bank Bangladesh', price: 35.40, change: 1.15, volume: 1400000 },
    { symbol: 'PRIME', name: 'Prime Bank Limited', price: 28.75, change: 0.50, volume: 820000 },
];

// Trading State
let selectedStock = null;
let orderType = 'buy'; // 'buy' or 'sell'
let userBalance = 100000.00;
let portfolio = [];
let orderHistory = [];
let priceChart = null;

// DOM Elements
const stockSearch = document.getElementById('stockSearch');
const stockList = document.getElementById('stockList');
const selectedStockInfo = document.getElementById('selectedStockInfo');
const selectedSymbol = document.getElementById('selectedSymbol');
const selectedPrice = document.getElementById('selectedPrice');
const selectedChange = document.getElementById('selectedChange');
const selectedVolume = document.getElementById('selectedVolume');
const buyBtn = document.getElementById('buyBtn');
const sellBtn = document.getElementById('sellBtn');
const orderQuantity = document.getElementById('orderQuantity');
const orderPrice = document.getElementById('orderPrice');
const useMarketPrice = document.getElementById('useMarketPrice');
const totalAmount = document.getElementById('totalAmount');
const placeOrderBtn = document.getElementById('placeOrderBtn');
const userBalanceEl = document.getElementById('userBalance');
const chartSymbol = document.getElementById('chartSymbol');
const portfolioList = document.getElementById('portfolioList');
const orderHistoryEl = document.getElementById('orderHistory');

// Safety check
if (!orderHistoryEl) {
    console.error('orderHistory element not found!');
}
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');

// API Base URL
const API_BASE_URL = '/api';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    renderStockList();
    setupEventListeners();
    updateMarketIndices();
    setInterval(updateStockPrices, 5000); // Update prices every 5 seconds
    
    // Set default balance first (in case API is slow)
    userBalanceEl.textContent = `৳${userBalance.toFixed(2)}`;
    
    // Load user's trading data from backend
    await loadTradingData();
});

// Render Stock List
function renderStockList(filteredStocks = null) {
    const stocks = filteredStocks || bangladeshiStocks;
    stockList.innerHTML = '';
    
    stocks.forEach(stock => {
        const stockItem = document.createElement('div');
        stockItem.className = `p-3 border-2 rounded-lg cursor-pointer transition-all hover:border-indigo-500 hover:bg-indigo-50 ${
            selectedStock?.symbol === stock.symbol ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'
        }`;
        stockItem.innerHTML = `
            <div class="flex justify-between items-center mb-1">
                <span class="font-semibold text-gray-800">${stock.symbol}</span>
                <span class="text-lg font-bold ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}">
                    ৳${stock.price.toFixed(2)}
                </span>
            </div>
            <div class="flex justify-between text-sm text-gray-600">
                <span>${stock.name}</span>
                <span class="${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}">
                    ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}%
                </span>
            </div>
        `;
        stockItem.addEventListener('click', () => selectStock(stock));
        stockList.appendChild(stockItem);
    });
}

// Select Stock
function selectStock(stock) {
    selectedStock = stock;
    selectedStockInfo.classList.remove('hidden');
    selectedSymbol.textContent = stock.symbol;
    selectedPrice.textContent = `৳${stock.price.toFixed(2)}`;
    selectedChange.textContent = `${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}%`;
    selectedChange.className = stock.change >= 0 ? 'font-semibold text-green-600' : 'font-semibold text-red-600';
    selectedVolume.textContent = (stock.volume / 1000).toFixed(1) + 'K';
    
    orderPrice.value = stock.price.toFixed(2);
    chartSymbol.textContent = stock.symbol;
    updateTotalAmount();
    updateChart(stock);
    renderStockList();
    placeOrderBtn.disabled = false;
}

// Setup Event Listeners
function setupEventListeners() {
    // Stock Search
    stockSearch.addEventListener('input', (e) => {
        const query = e.target.value.toUpperCase();
        const filtered = bangladeshiStocks.filter(stock => 
            stock.symbol.includes(query) || stock.name.toUpperCase().includes(query)
        );
        renderStockList(filtered);
    });

    // Order Type Buttons
    buyBtn.addEventListener('click', () => {
        orderType = 'buy';
        buyBtn.classList.add('border-green-500');
        buyBtn.classList.remove('border-transparent');
        sellBtn.classList.remove('border-red-500');
        sellBtn.classList.add('border-transparent');
        updateTotalAmount();
    });

    sellBtn.addEventListener('click', () => {
        orderType = 'sell';
        sellBtn.classList.add('border-red-500');
        sellBtn.classList.remove('border-transparent');
        buyBtn.classList.remove('border-green-500');
        buyBtn.classList.add('border-transparent');
        updateTotalAmount();
    });

    // Quantity and Price Inputs
    orderQuantity.addEventListener('input', updateTotalAmount);
    orderPrice.addEventListener('input', updateTotalAmount);

    // Use Market Price
    useMarketPrice.addEventListener('click', () => {
        if (selectedStock) {
            orderPrice.value = selectedStock.price.toFixed(2);
            updateTotalAmount();
        }
    });

    // Place Order
    placeOrderBtn.addEventListener('click', placeOrder);
}

// Update Total Amount
function updateTotalAmount() {
    const quantity = parseFloat(orderQuantity.value) || 0;
    const price = parseFloat(orderPrice.value) || 0;
    const total = quantity * price;
    totalAmount.textContent = `৳${total.toFixed(2)}`;
}

// Load trading data from backend
async function loadTradingData() {
    try {
        const response = await fetch(`${API_BASE_URL}/trading-data/`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (response.ok) {
            const data = await response.json();
            userBalance = data.balance || 100000.00;
            portfolio = data.portfolio || [];
            orderHistory = data.orders || [];
            
            console.log('Loaded trading data:', {
                balance: userBalance,
                portfolioCount: portfolio.length,
                orderCount: orderHistory.length,
                orders: orderHistory
            });
            
            // Update UI
            userBalanceEl.textContent = `৳${userBalance.toFixed(2)}`;
            renderPortfolio();
            
            // Ensure orderHistoryEl exists before rendering
            if (orderHistoryEl) {
                renderOrderHistory();
            } else {
                console.error('Cannot render order history: element not found');
            }
        } else {
            // If not authenticated, show message
            if (response.status === 401) {
                showToast('Please login to access trading platform', 'error');
                setTimeout(() => {
                    window.location.href = '/login/?next=/trading/';
                }, 2000);
            } else {
                // Try to get error message
                const errorData = await response.json().catch(() => ({}));
                console.error('Error loading trading data:', response.status, errorData);
                // Set default balance if API fails
                userBalance = 100000.00;
                userBalanceEl.textContent = `৳${userBalance.toFixed(2)}`;
                showToast('Failed to load trading data. Using default balance.', 'error');
            }
        }
    } catch (error) {
        console.error('Error loading trading data:', error);
        // Set default balance if API fails
        userBalance = 100000.00;
        userBalanceEl.textContent = `৳${userBalance.toFixed(2)}`;
        showToast('Error connecting to server. Using default balance.', 'error');
    }
}

// Place Order
async function placeOrder() {
    if (!selectedStock) {
        showToast('Please select a stock', 'error');
        return;
    }

    const quantity = parseInt(orderQuantity.value);
    const price = parseFloat(orderPrice.value);

    if (!quantity || quantity <= 0) {
        showToast('Please enter a valid quantity', 'error');
        return;
    }

    if (!price || price <= 0) {
        showToast('Please enter a valid price', 'error');
        return;
    }

    // Disable button during request
    placeOrderBtn.disabled = true;
    placeOrderBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';

    try {
        const response = await fetch(`${API_BASE_URL}/trading-data/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                symbol: selectedStock.symbol,
                type: orderType.toUpperCase(),
                quantity: quantity,
                price: price
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Update local state
            userBalance = data.balance;
            
            console.log('Order placed successfully, reloading data...');
            
            // Reload all data to get updated portfolio and orders
            await loadTradingData();
            
            // Update UI
            userBalanceEl.textContent = `৳${userBalance.toFixed(2)}`;
            updateTotalAmount();
            showToast(`${orderType === 'buy' ? 'Buy' : 'Sell'} order placed successfully!`, 'success');

            // Reset form
            orderQuantity.value = '';
            orderPrice.value = selectedStock.price.toFixed(2);
        } else {
            const errorMsg = data.error || 'Failed to place order';
            console.error('Order placement error:', errorMsg);
            showToast(errorMsg, 'error');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        showToast('An error occurred. Please try again.', 'error');
    } finally {
        placeOrderBtn.disabled = false;
        placeOrderBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Place Order';
    }
}

// Portfolio functions are now handled by backend - data is loaded from API

// Render Portfolio
function renderPortfolio() {
    if (portfolio.length === 0) {
        portfolioList.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fas fa-inbox text-4xl mb-2"></i>
                <p>No holdings yet</p>
            </div>
        `;
        return;
    }

    portfolioList.innerHTML = '';
    portfolio.forEach(holding => {
        const stock = bangladeshiStocks.find(s => s.symbol === holding.symbol);
        if (!stock) return;

        const avgPrice = parseFloat(holding.avg_price || holding.avgPrice);
        const quantity = parseInt(holding.quantity);
        const currentValue = quantity * stock.price;
        const totalCost = quantity * avgPrice;
        const profit = currentValue - totalCost;
        const profitPercent = totalCost > 0 ? ((profit / totalCost) * 100) : 0;

        const portfolioItem = document.createElement('div');
        portfolioItem.className = 'p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 transition-colors';
        portfolioItem.innerHTML = `
            <div class="flex justify-between items-center mb-2">
                <span class="font-semibold text-gray-800">${holding.symbol}</span>
                <span class="text-lg font-bold ${profit >= 0 ? 'text-green-600' : 'text-red-600'}">
                    ৳${currentValue.toFixed(2)}
                </span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-sm text-gray-600">
                <div>
                    <span>Qty: ${quantity}</span>
                </div>
                <div>
                    <span>Avg: ৳${avgPrice.toFixed(2)}</span>
                </div>
                <div class="col-span-2">
                    <span>P/L: <span class="${profit >= 0 ? 'text-green-600' : 'text-red-600'} font-semibold">
                        ${profit >= 0 ? '+' : ''}৳${profit.toFixed(2)} (${profitPercent >= 0 ? '+' : ''}${profitPercent.toFixed(2)}%)
                    </span></span>
                </div>
            </div>
        `;
        portfolioList.appendChild(portfolioItem);
    });
}

// Render Order History
function renderOrderHistory() {
    if (!orderHistoryEl) {
        console.error('orderHistoryEl element not found, cannot render order history');
        return;
    }
    
    console.log('Rendering order history, count:', orderHistory ? orderHistory.length : 0);
    console.log('Order history data:', orderHistory);
    
    if (!orderHistory || orderHistory.length === 0) {
        orderHistoryEl.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fas fa-clock text-4xl mb-2"></i>
                <p>No orders yet</p>
            </div>
        `;
        return;
    }

    orderHistoryEl.innerHTML = '';
    orderHistory.slice(0, 50).forEach((order, index) => {
        console.log(`Rendering order ${index}:`, order);
        
        const orderItem = document.createElement('div');
        const orderType = (order.type || order.order_type || '').toUpperCase();
        const timestamp = order.timestamp ? new Date(order.timestamp) : new Date();
        const price = parseFloat(order.price || 0);
        const quantity = parseInt(order.quantity || 0);
        const total = parseFloat(order.total || order.total_amount || (price * quantity));
        
        orderItem.className = `p-3 border-2 rounded-lg mb-2 ${
            orderType === 'BUY' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
        }`;
        orderItem.innerHTML = `
            <div class="flex justify-between items-center mb-1">
                <span class="font-semibold text-gray-800">${order.symbol || 'N/A'}</span>
                <span class="px-2 py-1 rounded text-xs font-semibold ${
                    orderType === 'BUY' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                }">
                    ${orderType}
                </span>
            </div>
            <div class="flex justify-between text-sm text-gray-600 mb-1">
                <span>${quantity} shares @ ৳${price.toFixed(2)}</span>
                <span class="font-semibold text-gray-800">৳${total.toFixed(2)}</span>
            </div>
            <div class="text-xs text-gray-500">
                <i class="fas fa-calendar mr-1"></i>${timestamp.toLocaleString('en-US', { 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit' 
                })}
            </div>
        `;
        orderHistoryEl.appendChild(orderItem);
    });
    
    console.log('Order history rendered, items:', orderHistoryEl.children.length);
}

// Update Stock Prices (Simulate real-time updates)
function updateStockPrices() {
    bangladeshiStocks.forEach(stock => {
        const change = (Math.random() - 0.5) * 0.5; // Random change between -0.25% to +0.25%
        stock.price = Math.max(1, stock.price * (1 + change / 100));
        stock.change = (Math.random() - 0.5) * 2;
        stock.volume += Math.floor(Math.random() * 10000);
    });

    if (selectedStock) {
        const updated = bangladeshiStocks.find(s => s.symbol === selectedStock.symbol);
        if (updated) {
            selectStock(updated);
        }
    }

    renderStockList();
    renderPortfolio();
}

// Update Market Indices
function updateMarketIndices() {
    // Simulate market indices
    const dsexIndex = document.getElementById('dsexIndex');
    const totalVolumeEl = document.getElementById('totalVolume');
    const advancersEl = document.getElementById('advancers');
    const declinersEl = document.getElementById('decliners');

    setInterval(() => {
        const currentIndex = parseFloat(dsexIndex.textContent.replace(/,/g, ''));
        const change = (Math.random() - 0.5) * 10;
        dsexIndex.textContent = (currentIndex + change).toFixed(2);
        
        const totalVol = bangladeshiStocks.reduce((sum, s) => sum + s.volume, 0);
        totalVolumeEl.textContent = (totalVol / 1000000).toFixed(1) + 'M';
        
        const adv = bangladeshiStocks.filter(s => s.change > 0).length;
        const dec = bangladeshiStocks.filter(s => s.change < 0).length;
        advancersEl.textContent = adv;
        declinersEl.textContent = dec;
    }, 3000);
}

// Update Chart
function updateChart(stock) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // Generate historical data
    const labels = [];
    const data = [];
    const now = new Date();
    
    for (let i = 30; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        const basePrice = stock.price * (0.9 + Math.random() * 0.2);
        data.push(parseFloat(basePrice.toFixed(2)));
    }

    if (priceChart) {
        priceChart.destroy();
    }

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${stock.symbol} Price`,
                data: data,
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '৳' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// Show Toast
function showToast(message, type = 'success') {
    toastMessage.textContent = message;
    toast.className = `fixed top-20 right-4 px-6 py-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white`;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Portfolio and order history are loaded from backend in loadTradingData()
// No need to initialize here - data loads when page loads

