import hashlib
import math
import requests
from datetime import datetime, timedelta
from flask import current_app


def deg_to_compass(num: float) -> str:
    """Convert meteorological wind degrees to cardinal direction."""
    val = int((num / 22.5) + .5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]


class WeatherService:
    """Handles communication with OpenWeatherMap API and realistic fallback simulations."""

    @classmethod
    def get_api_key(cls) -> str:
        return current_app.config.get('OPENWEATHER_API_KEY', '').strip()

    @classmethod
    def get_base_url(cls) -> str:
        return current_app.config.get('OPENWEATHER_BASE_URL', 'https://api.openweathermap.org/data/2.5')

    @classmethod
    def get_current_weather(cls, city: str, units: str = 'metric') -> dict:
        """Fetch current weather for a specified city name."""
        api_key = cls.get_api_key()
        if api_key and api_key != 'your_openweathermap_api_key_here':
            try:
                url = f"{cls.get_base_url()}/weather"
                params = {'q': city, 'appid': api_key, 'units': units}
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return cls._format_current_weather(data, units, is_mock=False)
                elif resp.status_code == 404:
                    return {'error': f"City '{city}' not found.", 'status_code': 404}
            except Exception as e:
                current_app.logger.warning(f"OpenWeatherMap request failed: {e}. Falling back to simulated data.")

        # Fallback realistic simulated weather (allows instant testing without requiring active paid API key)
        return cls._generate_mock_weather(city, units=units)

    @classmethod
    def get_weather_by_coords(cls, lat: float, lon: float, units: str = 'metric') -> dict:
        """Fetch current weather for geographic coordinates (GPS)."""
        api_key = cls.get_api_key()
        if api_key and api_key != 'your_openweathermap_api_key_here':
            try:
                url = f"{cls.get_base_url()}/weather"
                params = {'lat': lat, 'lon': lon, 'appid': api_key, 'units': units}
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return cls._format_current_weather(data, units, is_mock=False)
            except Exception as e:
                current_app.logger.warning(f"OpenWeatherMap coords request failed: {e}. Falling back to simulation.")

        city_name = f"Location ({round(lat, 2)}, {round(lon, 2)})"
        return cls._generate_mock_weather(city_name, units=units, lat=lat, lon=lon)

    @classmethod
    def get_forecast(cls, city: str = None, lat: float = None, lon: float = None, units: str = 'metric') -> dict:
        """Fetch 5-day / 3-hour forecast for city or coordinates."""
        api_key = cls.get_api_key()
        if api_key and api_key != 'your_openweathermap_api_key_here':
            try:
                url = f"{cls.get_base_url()}/forecast"
                params = {'appid': api_key, 'units': units}
                if city:
                    params['q'] = city
                elif lat is not None and lon is not None:
                    params['lat'] = lat
                    params['lon'] = lon

                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return cls._format_forecast(data, units, is_mock=False)
            except Exception as e:
                current_app.logger.warning(f"Forecast request failed: {e}. Falling back to simulation.")

        return cls._generate_mock_forecast(city or "Selected City", units=units)

    @classmethod
    def _format_current_weather(cls, data: dict, units: str, is_mock: bool = False) -> dict:
        """Transform raw OpenWeatherMap response into clean standard dictionary."""
        main = data.get('main', {})
        wind = data.get('wind', {})
        weather = data.get('weather', [{}])[0]
        sys_data = data.get('sys', {})
        coord = data.get('coord', {})
        deg = wind.get('deg', 0)

        # Timestamps
        sunrise_ts = sys_data.get('sunrise')
        sunset_ts = sys_data.get('sunset')
        sunrise_str = datetime.fromtimestamp(sunrise_ts).strftime('%I:%M %p') if sunrise_ts else '06:15 AM'
        sunset_str = datetime.fromtimestamp(sunset_ts).strftime('%I:%M %p') if sunset_ts else '06:45 PM'

        return {
            'city': data.get('name', 'Unknown'),
            'country': sys_data.get('country', ''),
            'coord': {'lat': coord.get('lat', 0.0), 'lon': coord.get('lon', 0.0)},
            'temp': round(main.get('temp', 0), 1),
            'feels_like': round(main.get('feels_like', 0), 1),
            'temp_min': round(main.get('temp_min', 0), 1),
            'temp_max': round(main.get('temp_max', 0), 1),
            'humidity': main.get('humidity', 0),
            'pressure': main.get('pressure', 1013),
            'wind_speed': round(wind.get('speed', 0), 1),
            'wind_deg': deg,
            'wind_dir': deg_to_compass(deg),
            'visibility': round(data.get('visibility', 10000) / 1000, 1),  # in km
            'condition': weather.get('main', 'Clear'),
            'description': weather.get('description', 'clear sky').title(),
            'icon': weather.get('icon', '01d'),
            'sunrise': sunrise_str,
            'sunset': sunset_str,
            'units': units,
            'unit_symbol': '°C' if units == 'metric' else '°F',
            'speed_symbol': 'm/s' if units == 'metric' else 'mph',
            'is_mock': is_mock,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }

    @classmethod
    def _format_forecast(cls, data: dict, units: str, is_mock: bool = False) -> dict:
        """Format 5-day / 3-hour forecast for display and Chart.js."""
        forecast_list = data.get('list', [])
        chart_labels = []
        chart_temps = []
        chart_humidity = []
        chart_rain_pop = []
        chart_wind = []

        # Daily aggregations
        daily_dict = {}

        for item in forecast_list:
            dt = datetime.fromtimestamp(item.get('dt', 0))
            day_key = dt.strftime('%Y-%m-%d')
            day_name = dt.strftime('%a, %b %d')
            time_label = dt.strftime('%a %I %p')

            temp = round(item.get('main', {}).get('temp', 0), 1)
            hum = item.get('main', {}).get('humidity', 0)
            pop = round(item.get('pop', 0) * 100)  # probability of precipitation %
            wind_spd = round(item.get('wind', {}).get('speed', 0), 1)

            # Chart entries (limit to 12 points / 36 hours for clarity)
            if len(chart_labels) < 12:
                chart_labels.append(time_label)
                chart_temps.append(temp)
                chart_humidity.append(hum)
                chart_rain_pop.append(pop)
                chart_wind.append(wind_spd)

            # Group for 5 daily summaries
            if day_key not in daily_dict:
                weather_info = item.get('weather', [{}])[0]
                daily_dict[day_key] = {
                    'date': day_key,
                    'day_name': day_name,
                    'temps': [temp],
                    'condition': weather_info.get('main', 'Clear'),
                    'description': weather_info.get('description', 'Clear sky').title(),
                    'icon': weather_info.get('icon', '01d'),
                    'max_pop': pop,
                    'humidity': hum
                }
            else:
                daily_dict[day_key]['temps'].append(temp)
                if pop > daily_dict[day_key]['max_pop']:
                    daily_dict[day_key]['max_pop'] = pop

        daily_forecast = []
        for d in list(daily_dict.values())[:5]:
            daily_forecast.append({
                'date': d['date'],
                'day_name': d['day_name'],
                'temp_min': min(d['temps']),
                'temp_max': max(d['temps']),
                'temp_avg': round(sum(d['temps']) / len(d['temps']), 1),
                'condition': d['condition'],
                'description': d['description'],
                'icon': d['icon'],
                'rain_pop': d['max_pop'],
                'humidity': d['humidity']
            })

        return {
            'daily': daily_forecast,
            'chart': {
                'labels': chart_labels,
                'temperatures': chart_temps,
                'humidity': chart_humidity,
                'rain_pop': chart_rain_pop,
                'wind': chart_wind
            },
            'is_mock': is_mock
        }

    @classmethod
    def _generate_mock_weather(cls, city: str, units: str = 'metric', lat: float = None, lon: float = None) -> dict:
        """Deterministic simulation for any city name so demo works flawlessly without API key."""
        clean_name = city.strip().title()
        hash_val = int(hashlib.md5(clean_name.encode('utf-8')).hexdigest()[:6], 16)
        
        # Determine simulated temperature range based on hash
        base_temp_c = 12 + (hash_val % 22)  # 12°C to 34°C
        temp = base_temp_c if units == 'metric' else round((base_temp_c * 9/5) + 32, 1)
        feels_like = temp + (1 if hash_val % 2 == 0 else -1.5)
        humidity = 40 + (hash_val % 55)
        pressure = 1005 + (hash_val % 25)
        wind_speed = round(2.5 + ((hash_val % 100) / 10), 1)
        wind_deg = hash_val % 360

        conditions = [
            ("Clear", "Clear sky", "01d"),
            ("Clouds", "Scattered clouds", "03d"),
            ("Rain", "Moderate rain shower", "10d"),
            ("Thunderstorm", "Thunderstorm with rain", "11d"),
            ("Drizzle", "Light drizzle", "09d"),
            ("Clouds", "Overcast clouds", "04d")
        ]
        cond, desc, icon = conditions[hash_val % len(conditions)]

        if lat is None or lon is None:
            lat = round(10.0 + (hash_val % 50), 4)
            lon = round(-120.0 + (hash_val % 240), 4)

        return {
            'city': clean_name,
            'country': 'INT',
            'coord': {'lat': lat, 'lon': lon},
            'temp': round(temp, 1),
            'feels_like': round(feels_like, 1),
            'temp_min': round(temp - 3, 1),
            'temp_max': round(temp + 3.5, 1),
            'humidity': humidity,
            'pressure': pressure,
            'wind_speed': wind_speed,
            'wind_deg': wind_deg,
            'wind_dir': deg_to_compass(wind_deg),
            'visibility': 10.0,
            'condition': cond,
            'description': desc,
            'icon': icon,
            'sunrise': '06:12 AM',
            'sunset': '06:48 PM',
            'units': units,
            'unit_symbol': '°C' if units == 'metric' else '°F',
            'speed_symbol': 'm/s' if units == 'metric' else 'mph',
            'is_mock': True,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }

    @classmethod
    def _generate_mock_forecast(cls, city: str, units: str = 'metric') -> dict:
        """Deterministic 5-day forecast simulation."""
        hash_val = int(hashlib.md5(city.encode('utf-8')).hexdigest()[:6], 16)
        base_temp_c = 15 + (hash_val % 18)
        base_temp = base_temp_c if units == 'metric' else (base_temp_c * 9/5) + 32

        now = datetime.now()
        chart_labels = []
        chart_temps = []
        chart_humidity = []
        chart_rain_pop = []
        chart_wind = []

        for i in range(12):
            dt = now + timedelta(hours=i * 3)
            temp_var = base_temp + round(3 * math.sin(i / 2), 1)
            pop = min(95, max(5, int(20 + 40 * math.cos(i))))
            hum = min(95, max(30, int(50 + 25 * math.sin(i))))
            wind = round(3.0 + 2 * math.cos(i), 1)

            chart_labels.append(dt.strftime('%a %I %p'))
            chart_temps.append(temp_var)
            chart_humidity.append(hum)
            chart_rain_pop.append(pop)
            chart_wind.append(wind)

        condition_pool = [
            ("Clear", "Sunny & clear", "01d"),
            ("Clouds", "Partly cloudy", "02d"),
            ("Rain", "Intermittent showers", "10d"),
            ("Clouds", "Broken clouds", "04d"),
            ("Thunderstorm", "Thunderstorms likely", "11d")
        ]

        daily_forecast = []
        for d in range(5):
            day_date = now + timedelta(days=d)
            cond_item = condition_pool[(hash_val + d) % len(condition_pool)]
            day_temp = base_temp + ((d - 2) * 1.5)
            daily_forecast.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'day_name': day_date.strftime('%a, %b %d'),
                'temp_min': round(day_temp - 2.5, 1),
                'temp_max': round(day_temp + 3.8, 1),
                'temp_avg': round(day_temp, 1),
                'condition': cond_item[0],
                'description': cond_item[1],
                'icon': cond_item[2],
                'rain_pop': min(90, max(10, 15 + (d * 18) % 80)),
                'humidity': min(90, max(40, 45 + (d * 10) % 50))
            })

        return {
            'daily': daily_forecast,
            'chart': {
                'labels': chart_labels,
                'temperatures': chart_temps,
                'humidity': chart_humidity,
                'rain_pop': chart_rain_pop,
                'wind': chart_wind
            },
            'is_mock': True
        }

    @classmethod
    def evaluate_alerts(cls, weather: dict, forecast: dict = None) -> list:
        """Scan current weather and forecast for severe/extreme conditions and generate alerts."""
        alerts = []
        temp = weather.get('temp', 20)
        units = weather.get('units', 'metric')
        temp_c = temp if units == 'metric' else (temp - 32) * 5/9
        wind_speed = weather.get('wind_speed', 0)
        wind_m_s = wind_speed if units == 'metric' else wind_speed * 0.44704
        cond = weather.get('condition', '').lower()
        desc = weather.get('description', '').lower()

        # 1. Extreme Heat Alert
        if temp_c >= 35:
            alerts.append({
                'level': 'danger',
                'type': 'Extreme Heat Warning',
                'icon': 'fa-temperature-high',
                'message': f"Extreme high temperature ({weather.get('temp')}{weather.get('unit_symbol')}). High risk of heat exhaustion; stay hydrated and seek shade."
            })
        elif temp_c <= 0:
            alerts.append({
                'level': 'info',
                'type': 'Freezing Frost Alert',
                'icon': 'fa-snowflake',
                'message': f"Sub-zero temperature ({weather.get('temp')}{weather.get('unit_symbol')}). Freezing conditions; watch out for black ice on roads."
            })

        # 2. Storm and Heavy Rain Alerts
        if 'thunderstorm' in cond or 'thunderstorm' in desc:
            alerts.append({
                'level': 'danger',
                'type': 'Severe Thunderstorm Warning',
                'icon': 'fa-bolt',
                'message': 'Severe lightning, localized squalls, and heavy downpours detected. Avoid open fields and stay indoors.'
            })
        elif 'rain' in cond or 'shower' in desc:
            if weather.get('humidity', 0) > 85:
                alerts.append({
                    'level': 'warning',
                    'type': 'Heavy Rainfall Alert',
                    'icon': 'fa-cloud-showers-heavy',
                    'message': 'Heavy precipitation expected. Reduced road visibility and water accumulation possible.'
                })

        # 3. High Wind Warning
        if wind_m_s >= 15:
            alerts.append({
                'level': 'warning',
                'type': 'High Wind Gale Warning',
                'icon': 'fa-wind',
                'message': f"High wind speeds of {weather.get('wind_speed')} {weather.get('speed_symbol')} ({weather.get('wind_dir')}). Secure loose outdoor objects."
            })

        # 4. Check upcoming forecast for rain probability spikes
        if forecast and forecast.get('daily'):
            first_day = forecast['daily'][0]
            if first_day.get('rain_pop', 0) >= 70 and not any(a['type'] == 'Heavy Rainfall Alert' for a in alerts):
                alerts.append({
                    'level': 'warning',
                    'type': 'High Rain Probability Alert',
                    'icon': 'fa-umbrella',
                    'message': f"{first_day.get('rain_pop')}% chance of rain in the coming hours. Carry an umbrella."
                })

        return alerts
