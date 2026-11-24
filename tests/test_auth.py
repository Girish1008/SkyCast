import unittest
from app import create_app, db
from app.models import User


class AuthTestCase(unittest.TestCase):
    """Test suite for authentication, hashing, and session management."""

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_user_registration(self):
        """Verify successful user registration and password hashing."""
        res = self.client.post('/auth/register', data={
            'username': 'johndoe',
            'email': 'john@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'John Doe',
            'preferred_units': 'metric',
            'default_city': 'London'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        user = User.query.filter_by(username='johndoe').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpass'))
        self.assertEqual(user.preferred_units, 'metric')

    def test_registration_password_mismatch(self):
        """Verify validation failure when passwords mismatch."""
        res = self.client.post('/auth/register', data={
            'username': 'mismatch',
            'email': 'mismatch@example.com',
            'password': 'password123',
            'confirm_password': 'differentpass',
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Passwords do not match', res.data)

    def test_user_login_success(self):
        """Verify user login with valid credentials."""
        user = User(username='alice', email='alice@example.com')
        user.set_password('Secret@123')
        db.session.add(user)
        db.session.commit()

        res = self.client.post('/auth/login', data={
            'identifier': 'alice',
            'password': 'Secret@123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back', res.data)

    def test_user_login_invalid_password(self):
        """Verify login rejection with incorrect credentials."""
        user = User(username='bob', email='bob@example.com')
        user.set_password('CorrectPass')
        db.session.add(user)
        db.session.commit()

        res = self.client.post('/auth/login', data={
            'identifier': 'bob',
            'password': 'WrongPassword'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Invalid username/email or password', res.data)


if __name__ == '__main__':
    unittest.main()
