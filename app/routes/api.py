from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import FavoriteCity, SearchHistory
from app.services.weather_service import WeatherService
from app.services.advisory_service import AdvisoryService

api_bp = Blueprint('api', __name__)


@api_bp.route('/weather', methods=['GET'])
def get_weather():
    """
    Main endpoint for comprehensive weather data:
    Current weather, 5-day forecast, severe alerts, and AI advisory recommendations.
    Query params:
      - city: city name (e.g. 'London')
      - lat, lon: coordinates
      - units: 'metric' (default) or 'imperial'
    """
    city = request.args.get('city', '').strip()
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)

    # Determine units: parameter or logged-in user's preference
    units = request.args.get('units')
    if not units:
        if current_user.is_authenticated:
            units = current_user.preferred_units or 'metric'
        else:
            units = 'metric'

    # Fetch current weather
    if lat is not None and lon is not None:
        weather_data = WeatherService.get_weather_by_coords(lat, lon, units=units)
        city_for_forecast = weather_data.get('city')
    elif city:
        weather_data = WeatherService.get_current_weather(city, units=units)
        city_for_forecast = city
    else:
        # Default fallback
        fallback_city = current_user.default_city if current_user.is_authenticated else "New York"
        weather_data = WeatherService.get_current_weather(fallback_city, units=units)
        city_for_forecast = fallback_city

    if 'error' in weather_data:
        return jsonify(weather_data), weather_data.get('status_code', 400)

    # Fetch 5-day forecast
    forecast_data = WeatherService.get_forecast(city=city_for_forecast, lat=lat, lon=lon, units=units)

    # Evaluate dynamic severe weather alerts
    alerts = WeatherService.evaluate_alerts(weather_data, forecast_data)

    # Generate AI / Smart Recommendations
    advisory = AdvisoryService.generate_recommendations(weather_data)

    # Record search history if user is logged in
    if current_user.is_authenticated and weather_data.get('city'):
        try:
            history_entry = SearchHistory(
                user_id=current_user.id,
                query_text=weather_data.get('city'),
                temperature=weather_data.get('temp'),
                weather_condition=weather_data.get('condition'),
                icon=weather_data.get('icon')
            )
            db.session.add(history_entry)
            db.session.commit()
        except Exception:
            db.session.rollback()

    # Check if city is bookmarked by current user
    is_favorite = False
    if current_user.is_authenticated:
        fav = FavoriteCity.query.filter_by(
            user_id=current_user.id,
            city_name=weather_data.get('city')
        ).first()
        is_favorite = fav is not None

    return jsonify({
        'success': True,
        'current': weather_data,
        'forecast': forecast_data,
        'alerts': alerts,
        'advisory': advisory,
        'is_favorite': is_favorite
    })


@api_bp.route('/favorites', methods=['GET', 'POST'])
@login_required
def handle_favorites():
    """Get list of user favorites with live weather summaries, or add a new favorite."""
    if request.method == 'POST':
        data = request.get_json() or {}
        city_name = data.get('city_name', '').strip()
        country_code = data.get('country_code', '').strip()
        lat = data.get('latitude')
        lon = data.get('longitude')

        if not city_name:
            return jsonify({'success': False, 'error': 'City name is required'}), 400

        existing = FavoriteCity.query.filter_by(user_id=current_user.id, city_name=city_name).first()
        if existing:
            return jsonify({'success': False, 'error': f"'{city_name}' is already in your favorites."}), 409

        fav = FavoriteCity(
            user_id=current_user.id,
            city_name=city_name,
            country_code=country_code,
            latitude=lat,
            longitude=lon
        )
        db.session.add(fav)
        db.session.commit()

        return jsonify({'success': True, 'message': f"Added '{city_name}' to favorites.", 'favorite': fav.to_dict()}), 201

    # GET: return list with live weather for multi-city comparative dashboard
    favs = FavoriteCity.query.filter_by(user_id=current_user.id).all()
    units = current_user.preferred_units or 'metric'
    results = []

    for f in favs:
        live = WeatherService.get_current_weather(f.city_name, units=units)
        results.append({
            'id': f.id,
            'city_name': f.city_name,
            'country_code': f.country_code or live.get('country', ''),
            'temp': live.get('temp'),
            'condition': live.get('condition'),
            'description': live.get('description'),
            'icon': live.get('icon'),
            'humidity': live.get('humidity'),
            'wind_speed': live.get('wind_speed'),
            'unit_symbol': live.get('unit_symbol', '°C'),
            'speed_symbol': live.get('speed_symbol', 'm/s')
        })

    return jsonify({'success': True, 'favorites': results})


@api_bp.route('/favorites/<int:fav_id>', methods=['DELETE'])
@login_required
def delete_favorite(fav_id):
    """Remove a city from favorites."""
    fav = FavoriteCity.query.filter_by(id=fav_id, user_id=current_user.id).first()
    if not fav:
        return jsonify({'success': False, 'error': 'Favorite city not found'}), 404

    city_name = fav.city_name
    db.session.delete(fav)
    db.session.commit()
    return jsonify({'success': True, 'message': f"Removed '{city_name}' from favorites."})


@api_bp.route('/history', methods=['GET', 'DELETE'])
@login_required
def handle_history():
    """Retrieve or clear search history."""
    if request.method == 'DELETE':
        SearchHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Search history cleared successfully.'})

    history = SearchHistory.query.filter_by(user_id=current_user.id)\
        .order_by(SearchHistory.searched_at.desc()).limit(30).all()
    return jsonify({'success': True, 'history': [h.to_dict() for h in history]})
