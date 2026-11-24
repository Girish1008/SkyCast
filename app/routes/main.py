from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app.models import FavoriteCity, SearchHistory

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Public landing page."""
    return render_template('index.html')


@main_bp.route('/dashboard')
def dashboard():
    """Interactive Weather Management Dashboard."""
    default_city = "New York"
    preferred_units = "metric"

    if current_user.is_authenticated:
        default_city = current_user.default_city or "New York"
        preferred_units = current_user.preferred_units or "metric"

    return render_template('dashboard.html', initial_city=default_city, units=preferred_units)


@main_bp.route('/favorites')
@login_required
def favorites():
    """Manage and monitor bookmarked cities."""
    favs = FavoriteCity.query.filter_by(user_id=current_user.id).order_by(FavoriteCity.created_at.desc()).all()
    return render_template('favorites.html', favorites=favs, units=current_user.preferred_units)


@main_bp.route('/history')
@login_required
def history():
    """View past search logs."""
    history_items = SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.searched_at.desc()).limit(50).all()
    return render_template('history.html', history_items=history_items)
