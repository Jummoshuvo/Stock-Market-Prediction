# Bangladeshi Stock Market Prediction Web Application

A full-stack web application for predicting Bangladeshi stock market prices using Django backend and modern frontend technologies.

## Features

- **Real-time Stock Predictions**: Get predictions for tomorrow, next week, and next month
- **Historical Data Visualization**: Interactive charts showing price trends
- **Bangladeshi Stock Support**: Works with bdshare and stocksurferbd libraries
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **Django REST API**: Robust backend with RESTful API endpoints

## Technology Stack

### Frontend
- HTML5, CSS3, JavaScript
- Tailwind CSS (via CDN)
- Chart.js for data visualization
- Font Awesome icons

### Backend
- Django 4.2.7
- Django REST Framework
- bdshare / stocksurferbd (for Bangladeshi stock data)
- pandas, numpy (for data analysis and predictions)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

#### Quick Setup (Windows)
Run the setup script:
```powershell
.\setup.ps1
```
Or double-click `setup.bat`

#### Manual Setup

1. **Clone or navigate to the project directory**
   ```bash
   cd "D:\7th semester\stock market prediction"
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   - On Windows (PowerShell):
     ```powershell
     venv\Scripts\Activate.ps1
     ```
   - On Windows (CMD):
     ```bash
     venv\Scripts\activate
     ```
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Upgrade pip and setuptools (Important for Python 3.12)**
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   ```

5. **Install numpy first (for Python 3.12 compatibility)**
   ```bash
   pip install "numpy>=1.26.0"
   ```

6. **Install other dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional, for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Django development server**
   ```bash
   python manage.py runserver
   ```

8. **Open in browser**
   - Navigate to: `http://127.0.0.1:8000/`
   - Or: `http://localhost:8000/`

## Usage

1. Enter a Bangladeshi stock symbol (e.g., GP, SQUARE, BEXIMCO, RENATA)
2. Click "Get Prediction" button
3. View predictions, confidence levels, and recommendations
4. Explore the interactive price trend chart

## API Endpoints

### Predict Stock
- **URL**: `/api/predict/`
- **Method**: POST
- **Body**: `{"symbol": "GP"}`
- **Response**: JSON with predictions, current price, confidence, and historical data

### Get Stock List
- **URL**: `/api/stocks/`
- **Method**: GET
- **Response**: JSON list of available Bangladeshi stocks

## Project Structure

```
stock market prediction/
├── manage.py
├── requirements.txt
├── README.md
├── stockpredictor/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── predictor/
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py
│   └── urls.py
├── templates/
│   └── index.html
└── static/
    └── script.js
```

## Notes

- The application uses **bdshare** or **stocksurferbd** libraries to fetch real Bangladeshi stock market data
- If these libraries are not installed or fail to fetch data, the app will use mock data for demonstration
- Predictions are based on moving averages and trend analysis
- **Important**: Predictions are for educational purposes only and should not be considered as financial advice

## Troubleshooting

### Python 3.12 Installation Issues
If you get errors like `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`:
1. Upgrade setuptools: `pip install --upgrade setuptools`
2. Install numpy separately: `pip install "numpy>=1.26.0"`
3. See `INSTALL.md` for detailed troubleshooting

### Libraries not installing
If `bdshare` or `stocksurferbd` fail to install:
- The app will still work with mock data
- Check Python version compatibility
- Try installing from alternative sources

### CORS errors
- CORS is configured to allow all origins in development
- For production, update `CORS_ALLOWED_ORIGINS` in `settings.py`

### Static files not loading
- Run: `python manage.py collectstatic` (if needed)
- Check that `STATIC_URL` and `STATICFILES_DIRS` are correctly configured

## Development

To modify the prediction algorithm, edit `predictor/views.py` in the `predict_price_simple_moving_average` function.

## License

This project is for educational purposes only.

