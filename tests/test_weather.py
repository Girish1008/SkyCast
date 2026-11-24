import unittest
import json
from app import create_app, db
from app.models import User, FavoriteCity
from app.services.weather_service import WeatherService
from app.services.advisory_service import AdvisoryService


class WeatherTestCase(unittest.TestCase):
    """Test suite for Weather API, Advisory Engine, and Bookmarks."""

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Seed test user
        self.user = User(username='tester', email='tester@example.com')
        self.user.set_password('Pass123')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_weather_endpoint_by_city(self):
        """Verify /api/weather returns current weather, forecast, alerts, and advisory."""
        res = self.client.get('/api/weather?city=Paris&units=metric')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertTrue(data['success'])
        self.assertIn('current', data)
        self.assertIn('forecast', data)
        self.assertIn('alerts', data)
        self.assertIn('advisory', data)

        current = data['current']
        self.assertEqual(current['city'], 'Paris')
        self.assertIn('temp', current)
        self.assertIn('humidity', current)
        self.assertIn('wind_speed', current)
        self.assertIn('pressure', current)
        self.assertIn('unit_symbol', current)
        self.assertEqual(current['unit_symbol'], '°C')

    def test_weather_endpoint_by_coords(self):
        """Verify coordinate based lookup for GPS location."""
        res = self.client.get('/api/weather?lat=51.5074&lon=-0.1278&units=metric')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('current', data)

    def test_advisory_engine(self):
        """Verify AI advisory recommendations generation."""
        mock_weather = {
            'temp': 2,
            'units': 'metric',
            'humidity': 85,
            'wind_speed': 10,
            'condition': 'Rain',
            'visibility': 8
        }
        advisory = AdvisoryService.generate_recommendations(mock_weather)
        self.assertIn('clothing', advisory)
        self.assertIn('gear', advisory)
        self.assertIn('activities', advisory)
        self.assertIn('driving_index', advisory)

        # In cold rainy weather, heavy thermal or rain gear must be advised
        clothing_text = " ".join(advisory['clothing']).lower()
        self.assertTrue('thermal' in clothing_text or 'jacket' in clothing_text)

    def test_weather_alerts_evaluation(self):
        """Verify automated severe weather alert detection."""
        hot_weather = {
            'temp': 39,
            'units': 'metric',
            'humidity': 40,
            'wind_speed': 5,
            'condition': 'Clear'
        }
        alerts = WeatherService.evaluate_alerts(hot_weather)
        self.assertTrue(any(a['type'] == 'Extreme Heat Warning' for a in alerts))

    def test_favorites_api_flow(self):
        """Verify authenticated addition and listing of favorite cities."""
        # Login test user
        self.client.post('/auth/login', data={'identifier': 'tester', 'password': 'Pass123'})

        # Add favorite
        res = self.client.post('/api/favorites', json={
            'city_name': 'Singapore',
            'country_code': 'SG',
            'latitude': 1.3521,
            'longitude': 103.8198
        })
        self.assertEqual(res.status_code, 201)

        # Get favorites list
        get_res = self.client.get('/api/favorites')
        self.assertEqual(get_res.status_code, 200)
        fav_data = json.loads(get_res.data)
        self.assertTrue(fav_data['success'])
        self.assertEqual(len(fav_data['favorites']), 1)
        self.assertEqual(fav_data['favorites'][0]['city_name'], 'Singapore')


if __name__ == '__main__':
    unittest.main()
