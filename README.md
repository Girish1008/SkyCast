# SkyPulse Cloud: Weather Information Management System

A production-grade, responsive, full-stack Cloud-Based Weather Information Management System built using Python Flask, OpenWeatherMap REST APIs, MySQL/SQLite database persistence, and Chart.js telemetry dashboards.

---

## 1. System Architecture

```mermaid
graph TD
    User([Web Client / Mobile Browser]) <--> |HTTPS / Bootstrap 5 + JS| Flask[Flask Application Server / Gunicorn]
    Flask <--> |SQLAlchemy ORM| DB[(MySQL 8.0 / SQLite)]
    Flask <--> |REST API Requests| OWM[OpenWeatherMap Public API]
    Flask --> Engine[AI Condition Advisory & Alert Engine]
    Flask --> Cache[Telemetry Normalization & Fallback Simulator]
```

### Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ FAVORITE_CITIES : "bookmarks"
    USERS ||--o{ SEARCH_HISTORY : "logs"

    USERS {
        int id PK
        varchar username UK
        varchar email UK
        varchar password_hash
        varchar full_name
        varchar preferred_units
        varchar default_city
        timestamp created_at
    }

    FAVORITE_CITIES {
        int id PK
        int user_id FK
        varchar city_name
        varchar country_code
        decimal latitude
        decimal longitude
        timestamp created_at
    }

    SEARCH_HISTORY {
        int id PK
        int user_id FK
        varchar query_text
        decimal temperature
        varchar weather_condition
        varchar icon
        timestamp searched_at
    }
```

---

## 2. Key Features

1. **User Authentication & Profiles**
   - Secure account registration and login protected with cryptographic **Bcrypt** hashing.
   - User profile customization: full name, default city, and global unit preferences (°C Metric vs. °F Imperial).
2. **Real-Time Weather Telemetry**
   - Live temperature, "feels like" index, daily high/low temperatures.
   - Humidity percentage with visual gauge.
   - Wind speed and 16-point cardinal compass direction (e.g. `4.2 m/s WNW`).
   - Atmospheric pressure (hPa) and optical visibility range (km).
   - Sunrise and sunset astronomical timings.
3. **5-Day Visual Forecast Trajectory**
   - 5-day daily forecast cards with minimum/maximum temperature range, condition badges, and rain probabilities.
   - Interactive **Chart.js** telemetry visualizer:
     - Temperature trend line graph
     - Precipitation probability bar chart
     - Dual-axis humidity and wind velocity comparison
4. **Location-Based Weather Search**
   - Global city lookup with instant search.
   - Browser **HTML5 Geolocation API** (GPS coordinates) with one-click location detection.
   - Multi-city bookmarks with live comparison matrix.
5. **Severe Weather Alert Engine**
   - Dynamic real-time alerts for Extreme Heat (`>= 35°C`), Freezing Frost (`<= 0°C`), Severe Thunderstorms, Heavy Downpours, and High Wind Gales.
6. **AI Condition Advisory & Recommendations**
   - Intelligent clothing recommendations (winter coat, rain gear, light cottons).
   - Outdoor athletic suitability index for running, cycling, and hiking.
   - Road travel and driving safety index with fog/rain precautions.
   - Health and hydration recommendations.
   - Essential gear checklist (umbrella, sunglasses, thermal flask).

---

## 3. Project Directory Structure

```text
Cloud Mini Project/
├── app/
│   ├── __init__.py               # Application factory & extension registration
│   ├── config.py                 # Configuration classes (Dev, Prod, Testing)
│   ├── models.py                 # SQLAlchemy models (User, FavoriteCity, SearchHistory)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication & user profile endpoints
│   │   ├── main.py               # Web page view controllers (Home, Dashboard, Favorites, History)
│   │   └── api.py                # REST API endpoints (/api/weather, /api/favorites, /api/history)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── weather_service.py    # OpenWeatherMap API client + deterministic simulation fallback
│   │   └── advisory_service.py   # AI/Rule-based attire & activity recommendations
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css         # Modern styling, glassmorphism, responsive cards
│   │   └── js/
│   │       └── dashboard.js      # Fetch API, Chart.js charts, Geolocation, DOM updates
│   └── templates/
│       ├── base.html             # Base layout with navbar, alerts, footer
│       ├── index.html            # Landing hero page with quick search
│       ├── login.html            # User login page
│       ├── register.html         # User registration page
│       ├── dashboard.html        # Interactive weather management dashboard
│       ├── favorites.html        # Multi-city saved bookmarks matrix
│       ├── history.html          # Query audit trail
│       └── profile.html          # Profile settings and preferences
├── database/
│   └── schema.sql                # Complete MySQL DDL schema and sample seed queries
├── tests/
│   ├── __init__.py
│   ├── test_auth.py              # Authentication unit tests
│   └── test_weather.py           # Weather API and advisory engine unit tests
├── .dockerignore
├── .env.example                  # Environment configuration template
├── Dockerfile                    # Container definition for Cloud Run / AWS / Azure
├── docker-compose.yml            # Multi-container setup with MySQL 8.0 & Web app
├── requirements.txt              # Python package dependencies
├── run.py                        # Application entry point
└── README.md                     # Comprehensive project documentation
```

---

## 4. OpenWeatherMap API Integration

1. Register for a free API key at [OpenWeatherMap](https://openweathermap.org/api).
2. Generate your 32-character API key in your account dashboard.
3. Add the key to your `.env` file:
   ```bash
   OPENWEATHER_API_KEY=your_32_character_api_key_here
   ```
4. **Built-in Zero-Config Demo Mode:**
   If no API key is provided, the system automatically activates its built-in deterministic simulation engine. All endpoints, forecasts, charts, and recommendations continue to work seamlessly.

---

## 5. Local Installation & Execution

### Prerequisites
- Python 3.9+ installed
- MySQL (optional, SQLite is used out-of-the-box with zero configuration)

### Step-by-Step Setup

```bash
# 1. Clone or navigate to the project directory
cd "Cloud Mini Project"

# 2. Create and activate a Python virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env   # On Windows
# cp .env.example .env    # On Linux/macOS

# 5. Start the development server
python run.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

### Pre-seeded Demo Credentials
- **Username:** `admin`
- **Password:** `Admin@123`
*(Or click **Register** to create a new user profile immediately)*

---

## 6. Running Automated Tests

Run the complete automated unit test suite:

```bash
python -m unittest discover -s tests
```

---

## 7. Cloud Deployment Instructions

### Option A: Google Cloud Run (Recommended Containerized Cloud Deployment)

1. **Install and authenticate Google Cloud SDK:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```
2. **Build and deploy container directly to Cloud Run:**
   ```bash
   gcloud run deploy weather-cloud-app \
       --source . \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --set-env-vars "FLASK_ENV=production,SECRET_KEY=your-production-secret,OPENWEATHER_API_KEY=your_key"
   ```
3. Cloud Run will provide a live HTTPS URL (e.g. `https://weather-cloud-app-xyz.a.run.app`).

### Option B: AWS Elastic Beanstalk / ECS

1. Create a `Dockerrun.aws.json` or deploy via the AWS EB CLI:
   ```bash
   eb init -p docker weather-management-app
   eb create weather-prod-env
   ```
2. Configure Environment variables in AWS Console under **Configuration > Software**:
   - `SECRET_KEY`
   - `OPENWEATHER_API_KEY`
   - `DATABASE_URL` (pointing to your AWS RDS MySQL instance)

### Option C: Docker Compose (Local or Production VM)

To spin up the web application and MySQL 8.0 together:

```bash
docker-compose up --build -d
```
Access the application on `http://localhost:5000`.

---

## 8. Database Schema & SQL Execution

To deploy the schema to an external MySQL server (AWS RDS / GCP Cloud SQL / Local MySQL):

```bash
mysql -u root -p < database/schema.sql
```
Update your `.env`:
```ini
DATABASE_URL=mysql+pymysql://username:password@hostname:3306/weather_db
```
