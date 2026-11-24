from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt


class User(UserMixin, db.Model):
    """User account model for authentication and preferences."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    preferred_units = db.Column(db.String(10), default='metric')  # 'metric' (°C) or 'imperial' (°F)
    default_city = db.Column(db.String(100), default='New York')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    favorites = db.relationship('FavoriteCity', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str):
        """Hash and store password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name or self.username,
            'preferred_units': self.preferred_units,
            'default_city': self.default_city,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f'<User {self.username}>'


class FavoriteCity(db.Model):
    """Saved favorite cities per user."""
    __tablename__ = 'favorite_cities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    city_name = db.Column(db.String(100), nullable=False)
    country_code = db.Column(db.String(10), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'city_name', name='uq_user_city'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'city_name': self.city_name,
            'country_code': self.country_code or '',
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f'<FavoriteCity {self.city_name} (User {self.user_id})>'


class SearchHistory(db.Model):
    """User search history for auditing and quick access."""
    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    query_text = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float, nullable=True)
    weather_condition = db.Column(db.String(100), nullable=True)
    icon = db.Column(db.String(20), nullable=True)
    searched_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'query_text': self.query_text,
            'temperature': self.temperature,
            'weather_condition': self.weather_condition,
            'icon': self.icon,
            'searched_at': self.searched_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f'<SearchHistory {self.query_text} (User {self.user_id})>'
