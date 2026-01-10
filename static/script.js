// Stock Market Prediction Application - Connected to Django Backend

// API Base URL
const API_BASE_URL = '/api';

// DOM Elements
const stockSymbolInput = document.getElementById('stockSymbol');
const predictBtn = document.getElementById('predictBtn');
const currentPriceCard = document.getElementById('currentPriceCard');
const currentPrice = document.getElementById('currentPrice');
const predictionCard = document.getElementById('predictionCard');
const chartCard = document.getElementById('chartCard');
const welcomeMessage = document.getElementById('welcomeMessage');
const loadingState = document.getElementById('loadingState');

// Prediction result elements
const tomorrowPrice = document.getElementById('tomorrowPrice');
const tomorrowChange = document.getElementById('tomorrowChange');
const weekPrice = document.getElementById('weekPrice');
const weekChange = document.getElementById('weekChange');
const monthPrice = document.getElementById('monthPrice');
const monthChange = document.getElementById('monthChange');
const confidence = document.getElementById('confidence');
const confidenceBar = document.getElementById('confidenceBar');
const recommendationText = document.getElementById('recommendationText');

// Chart instance
let priceChart = null;

// Bangladeshi stock symbols for reference
const popularStocks = {
    'GP': 'Grameenphone Ltd',
    'SQUARE': 'Square Pharmaceuticals Ltd',
    'BEXIMCO': 'Beximco Pharmaceuticals Ltd',
    'RENATA': 'Renata Limited',
    'ACI': 'ACI Limited',
    'BRACBANK': 'BRAC Bank Limited',
    'EBL': 'Eastern Bank Limited',
    'DUTCHBANGLA': 'Dutch-Bangla Bank Limited',
    'BANKASIA': 'Bank Asia Limited',
    'IFIC': 'IFIC Bank Limited'
};

// Fetch prediction from Django API
async function fetchPrediction(symbol) {
    try {
        const response = await fetch(`${API_BASE_URL}/predict/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbol: symbol })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch prediction');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching prediction:', error);
        throw error;
    }
}

// Calculate percentage change
function calculateChange(current, predicted) {
    const change = ((predicted - current) / current) * 100;
    return {
        value: change,
        formatted: `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`,
        isPositive: change >= 0
    };
}

// Generate recommendation
function getRecommendation(prediction, currentPrice) {
    const avgChange = (
        (prediction.tomorrow - currentPrice) / currentPrice +
        (prediction.week - currentPrice) / currentPrice +
        (prediction.month - currentPrice) / currentPrice
    ) / 3 * 100;
    
    if (avgChange > 5) {
        return {
            text: "Strong buy recommendation. The stock shows positive momentum across all timeframes.",
            color: "text-green-600"
        };
    } else if (avgChange > 2) {
        return {
            text: "Buy recommendation. The stock is expected to perform well in the near future.",
            color: "text-green-600"
        };
    } else if (avgChange > -2) {
        return {
            text: "Hold recommendation. The stock shows mixed signals. Monitor closely.",
            color: "text-yellow-600"
        };
    } else if (avgChange > -5) {
        return {
            text: "Sell recommendation. Consider reducing your position as the stock may decline.",
            color: "text-orange-600"
        };
    } else {
        return {
            text: "Strong sell recommendation. The stock shows negative momentum across all timeframes.",
            color: "text-red-600"
        };
    }
}

// Create or update chart with historical and predicted data
function createChart(historicalData, currentPrice, prediction) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // Prepare labels
    const historicalLabels = historicalData.labels || [];
    const futureLabels = ['Today', 'Tomorrow', 'Next Week', 'Next Month'];
    const allLabels = [...historicalLabels, ...futureLabels];
    
    // Prepare historical data
    const historicalPrices = historicalData.data || [];
    const historicalDataPoints = [...historicalPrices, null, null, null, null];
    
    // Prepare predicted data
    const predictedDataPoints = new Array(historicalPrices.length).fill(null);
    predictedDataPoints.push(
        currentPrice,
        prediction.tomorrow,
        prediction.week,
        prediction.month
    );
    
    if (priceChart) {
        priceChart.destroy();
    }
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: 'Historical Price',
                    data: historicalDataPoints,
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3,
                    fill: true
                },
                {
                    label: 'Predicted Price',
                    data: predictedDataPoints,
                    borderColor: 'rgb(168, 85, 247)',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    borderDash: [5, 5],
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: 'rgb(168, 85, 247)',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += '৳' + context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
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

// Display prediction results
function displayResults(symbol, apiData) {
    // Show cards
    currentPriceCard.classList.remove('hidden');
    predictionCard.classList.remove('hidden');
    chartCard.classList.remove('hidden');
    welcomeMessage.classList.add('hidden');
    
    const currentPriceValue = apiData.current_price;
    const prediction = apiData.predictions;
    
    // Update current price
    currentPrice.textContent = `৳${currentPriceValue.toFixed(2)}`;
    
    // Calculate changes
    const tomorrowChangeData = calculateChange(currentPriceValue, prediction.tomorrow);
    const weekChangeData = calculateChange(currentPriceValue, prediction.week);
    const monthChangeData = calculateChange(currentPriceValue, prediction.month);
    
    // Update tomorrow prediction
    tomorrowPrice.textContent = `৳${prediction.tomorrow.toFixed(2)}`;
    tomorrowChange.textContent = tomorrowChangeData.formatted;
    tomorrowChange.className = `text-sm mt-1 font-semibold ${tomorrowChangeData.isPositive ? 'text-green-600' : 'text-red-600'}`;
    
    // Update week prediction
    weekPrice.textContent = `৳${prediction.week.toFixed(2)}`;
    weekChange.textContent = weekChangeData.formatted;
    weekChange.className = `text-sm mt-1 font-semibold ${weekChangeData.isPositive ? 'text-green-600' : 'text-red-600'}`;
    
    // Update month prediction
    monthPrice.textContent = `৳${prediction.month.toFixed(2)}`;
    monthChange.textContent = monthChangeData.formatted;
    monthChange.className = `text-sm mt-1 font-semibold ${monthChangeData.isPositive ? 'text-green-600' : 'text-red-600'}`;
    
    // Update confidence
    confidence.textContent = `${apiData.confidence}%`;
    confidenceBar.style.width = `${apiData.confidence}%`;
    
    // Update recommendation
    const recommendation = getRecommendation(prediction, currentPriceValue);
    recommendationText.textContent = recommendation.text;
    recommendationText.className = recommendation.color;
    
    // Create chart with historical data from API
    const historicalData = apiData.historical_data || { labels: [], data: [] };
    createChart(historicalData, currentPriceValue, prediction);
}

// Show error message
function showError(message) {
    alert('Error: ' + message);
    loadingState.classList.add('hidden');
    welcomeMessage.classList.remove('hidden');
}

// Handle prediction button click
predictBtn.addEventListener('click', async () => {
    const symbol = stockSymbolInput.value.trim().toUpperCase();
    
    if (!symbol) {
        alert('Please enter a stock symbol');
        return;
    }
    
    // Show loading state
    loadingState.classList.remove('hidden');
    predictionCard.classList.add('hidden');
    chartCard.classList.add('hidden');
    currentPriceCard.classList.add('hidden');
    welcomeMessage.classList.add('hidden');
    
    try {
        // Fetch prediction from Django API
        const apiData = await fetchPrediction(symbol);
        
        // Hide loading and show results
        loadingState.classList.add('hidden');
        displayResults(symbol, apiData);
        
        // Show info message if using mock data
        if (apiData.source === 'mock' && apiData.message) {
            console.warn(apiData.message);
        }
    } catch (error) {
        showError(error.message);
    }
});

// Allow Enter key to trigger prediction
stockSymbolInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        predictBtn.click();
    }
});

// Load popular stocks list on page load (optional)
async function loadStockList() {
    try {
        const response = await fetch(`${API_BASE_URL}/stocks/`);
        if (response.ok) {
            const data = await response.json();
            console.log('Available stocks:', data.stocks);
        }
    } catch (error) {
        console.log('Could not load stock list:', error);
    }
}

// Initialize on page load
window.addEventListener('load', () => {
    loadStockList();
});
