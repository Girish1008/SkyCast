/**
 * SkyPulse Cloud Weather System - Interactive Dashboard Controller
 * Powered by Fetch API, HTML5 Geolocation, and Chart.js
 */

let weatherChartInstance = null;
let currentWeatherData = null;
let currentForecastData = null;
let activeChartMetric = 'temp';

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('weatherSearchForm');
    const cityInput = document.getElementById('cityInput');
    const geoBtn = document.getElementById('geoBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const favoriteBtn = document.getElementById('favoriteBtn');
    const unitToggles = document.querySelectorAll('input[name="unitToggle"]');
    const metricTabs = document.querySelectorAll('#chartMetricTabs .nav-link');

    // Initial Weather Load
    const initialCity = cityInput.value.trim() || 'New York';
    loadWeather({ city: initialCity });

    // Search Form Submit
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const city = cityInput.value.trim();
        if (city) {
            loadWeather({ city });
        }
    });

    // GPS Geolocation Button
    geoBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            showAlert('Geolocation is not supported by your browser.', 'warning');
            return;
        }

        geoBtn.disabled = true;
        geoBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Locating...';

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                loadWeather({ lat, lon });
                geoBtn.disabled = false;
                geoBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs me-1"></i> Detect Location';
            },
            (err) => {
                geoBtn.disabled = false;
                geoBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs me-1"></i> Detect Location';
                let msg = 'Could not detect GPS location. Defaulting to city search.';
                if (err.code === 1) msg = 'Location permission was denied. Please allow location access.';
                showAlert(msg, 'warning');
            },
            { timeout: 10000 }
        );
    });

    // Refresh Button
    refreshBtn.addEventListener('click', () => {
        const city = cityInput.value.trim() || 'New York';
        loadWeather({ city });
    });

    // Unit Toggle Change (°C vs °F)
    unitToggles.forEach(toggle => {
        toggle.addEventListener('change', () => {
            const city = cityInput.value.trim() || 'New York';
            loadWeather({ city, units: toggle.value });
        });
    });

    // Chart Metric Tabs Switcher
    metricTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            metricTabs.forEach(t => t.classList.remove('active'));
            e.currentTarget.classList.add('active');
            activeChartMetric = e.currentTarget.dataset.metric;
            if (currentForecastData) {
                renderForecastChart(currentForecastData.chart, currentWeatherData ? currentWeatherData.unit_symbol : '°C');
            }
        });
    });

    // Favorite Button Handler
    favoriteBtn.addEventListener('click', async () => {
        const isAuth = favoriteBtn.dataset.auth === 'true';
        if (!isAuth) {
            if (confirm('You must be logged in to save favorite cities. Go to login page?')) {
                window.location.href = '/auth/login';
            }
            return;
        }

        if (!currentWeatherData || !currentWeatherData.city) return;

        favoriteBtn.disabled = true;
        try {
            const res = await fetch('/api/favorites', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    city_name: currentWeatherData.city,
                    country_code: currentWeatherData.country,
                    latitude: currentWeatherData.coord ? currentWeatherData.coord.lat : null,
                    longitude: currentWeatherData.coord ? currentWeatherData.coord.lon : null
                })
            });

            const data = await res.json();
            if (res.status === 201) {
                setFavoriteState(true);
                showAlert(`Saved '${currentWeatherData.city}' to your favorites!`, 'success');
            } else if (res.status === 409) {
                showAlert(`'${currentWeatherData.city}' is already saved in your favorites.`, 'info');
                setFavoriteState(true);
            } else {
                showAlert(data.error || 'Failed to save city', 'danger');
            }
        } catch (err) {
            showAlert('Network error while saving favorite.', 'danger');
        } finally {
            favoriteBtn.disabled = false;
        }
    });
});

/**
 * Fetch and coordinate weather telemetry from Flask API
 */
async function loadWeather({ city, lat, lon, units }) {
    const loading = document.getElementById('loadingIndicator');
    const content = document.getElementById('dashboardContent');
    const cityInput = document.getElementById('cityInput');

    const selectedUnits = units || document.querySelector('input[name="unitToggle"]:checked')?.value || 'metric';

    let url = `/api/weather?units=${selectedUnits}`;
    if (lat !== undefined && lon !== undefined) {
        url += `&lat=${lat}&lon=${lon}`;
    } else if (city) {
        url += `&city=${encodeURIComponent(city)}`;
    }

    loading.classList.remove('d-none');
    content.style.opacity = '0.4';

    try {
        const resp = await fetch(url);
        const data = await resp.json();

        loading.classList.add('d-none');
        content.style.opacity = '1';

        if (!resp.ok || data.error) {
            showAlert(data.error || 'City telemetry lookup failed.', 'danger');
            return;
        }

        currentWeatherData = data.current;
        currentForecastData = data.forecast;

        // Update City Search Input
        cityInput.value = data.current.city;

        // Populate DOM Components
        updateCurrentWeatherUI(data.current);
        updateTelemetryMetrics(data.current);
        updateAlertsUI(data.alerts);
        updateAdvisoryUI(data.advisory);
        updateForecastCardsUI(data.forecast.daily, data.current.unit_symbol);
        renderForecastChart(data.forecast.chart, data.current.unit_symbol);
        setFavoriteState(data.is_favorite);

    } catch (err) {
        loading.classList.add('d-none');
        content.style.opacity = '1';
        showAlert('Network or server error encountered while fetching weather telemetry.', 'danger');
    }
}

/**
 * Render Current Weather Hero Card
 */
function updateCurrentWeatherUI(w) {
    document.getElementById('cityName').textContent = `${w.city}${w.country ? ', ' + w.country : ''}`;
    document.getElementById('locationCoords').textContent = `Lat: ${w.coord.lat} • Lon: ${w.coord.lon}`;
    document.getElementById('currentTemp').textContent = `${w.temp}${w.unit_symbol}`;
    document.getElementById('weatherDesc').textContent = w.description;
    document.getElementById('feelsLike').textContent = `${w.feels_like}${w.unit_symbol}`;
    document.getElementById('tempMax').textContent = `${w.temp_max}${w.unit_symbol}`;
    document.getElementById('tempMin').textContent = `${w.temp_min}${w.unit_symbol}`;
    document.getElementById('sunriseTime').textContent = w.sunrise;
    document.getElementById('sunsetTime').textContent = w.sunset;

    const iconUrl = `https://openweathermap.org/img/wn/${w.icon}@2x.png`;
    document.getElementById('weatherIcon').src = iconUrl;
    document.getElementById('weatherIcon').alt = w.condition;

    // Station Status indicator
    const station = document.getElementById('stationStatus');
    if (w.is_mock) {
        station.innerHTML = '<i class="fa-solid fa-microchip text-warning me-1"></i> Demo Engine Telemetry';
        station.title = 'Deterministic demo telemetry (add OPENWEATHER_API_KEY to activate live satellite feed)';
    } else {
        station.innerHTML = '<i class="fa-solid fa-satellite text-success me-1"></i> OpenWeather Satellite Live';
    }
}

/**
 * Render Telemetry Metrics
 */
function updateTelemetryMetrics(w) {
    document.getElementById('humidityVal').textContent = `${w.humidity}%`;
    document.getElementById('humidityBar').style.width = `${w.humidity}%`;

    document.getElementById('windVal').textContent = `${w.wind_speed} ${w.speed_symbol}`;
    document.getElementById('windDirection').textContent = `Direction: ${w.wind_dir} (${w.wind_deg}°)`;

    document.getElementById('pressureVal').textContent = `${w.pressure} hPa`;
    document.getElementById('visibilityVal').textContent = `${w.visibility} km`;
}

/**
 * Render Dynamic Severe Weather Alerts
 */
function updateAlertsUI(alerts) {
    const container = document.getElementById('alertsContainer');
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = alerts.map(a => `
        <div class="alert alert-${a.level} alert-card-${a.level} shadow-sm d-flex align-items-center gap-3 p-3 mb-2 rounded-3" role="alert">
            <div class="fs-3"><i class="fa-solid ${a.icon}"></i></div>
            <div class="flex-grow-1">
                <div class="fw-bold">${a.type}</div>
                <div class="small">${a.message}</div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `).join('');
}

/**
 * Render AI Smart Condition Advisory
 */
function updateAdvisoryUI(adv) {
    if (!adv) return;

    // Clothing list
    const clothingEl = document.getElementById('clothingList');
    clothingEl.innerHTML = adv.clothing.map(c => `
        <li class="mb-1 text-muted"><i class="fa-solid fa-circle-check text-success me-2"></i>${c}</li>
    `).join('');

    // Activity
    const actBadge = document.getElementById('activityBadge');
    actBadge.textContent = adv.activity_status;
    actBadge.className = `badge ${adv.activity_score >= 4 ? 'bg-success-subtle text-success' : (adv.activity_score >= 3 ? 'bg-warning-subtle text-warning' : 'bg-danger-subtle text-danger')}`;
    document.getElementById('activityNote').textContent = adv.activity_notes;

    // Activities Breakdown
    const actBreakdown = document.getElementById('activitiesBreakdown');
    actBreakdown.innerHTML = Object.entries(adv.activities).map(([act, note]) => `
        <div class="d-flex justify-content-between py-1 border-bottom border-light">
            <span class="fw-semibold text-secondary">${act}:</span>
            <span class="text-muted">${note}</span>
        </div>
    `).join('');

    // Driving
    document.getElementById('drivingAdvice').innerHTML = `
        <strong>${adv.driving_index}:</strong> ${adv.driving_notes}
    `;

    // Gear
    const gearEl = document.getElementById('gearList');
    gearEl.innerHTML = adv.gear.map(g => `
        <span class="badge bg-light text-dark border"><i class="fa-solid fa-check text-primary me-1"></i>${g}</span>
    `).join('');
}

/**
 * Render 5-Day Extended Forecast Grid
 */
function updateForecastCardsUI(daily, unitSymbol) {
    const row = document.getElementById('forecastCardsRow');
    if (!daily || daily.length === 0) return;

    row.innerHTML = daily.map(d => `
        <div class="col-6 col-md-4 col-xl" style="flex: 1 0 18%;">
            <div class="forecast-card h-100">
                <div class="fw-bold small text-secondary">${d.day_name.split(',')[0]}</div>
                <div class="text-muted" style="font-size: 0.75rem;">${d.day_name.split(',')[1] || ''}</div>
                <img src="https://openweathermap.org/img/wn/${d.icon}@2x.png" alt="${d.condition}" class="forecast-icon">
                <div class="fw-extrabold text-primary fs-5">${Math.round(d.temp_max)}${unitSymbol}</div>
                <div class="text-muted small">${Math.round(d.temp_min)}${unitSymbol}</div>
                <div class="small text-truncate mt-1 text-muted" title="${d.description}">${d.condition}</div>
                <hr class="my-2 border-light">
                <div class="d-flex justify-content-center gap-2" style="font-size: 0.75rem;">
                    <span title="Rain Chance" class="text-info"><i class="fa-solid fa-droplet me-1"></i>${d.rain_pop}%</span>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Render Chart.js Forecast Trajectory
 */
function renderForecastChart(chartData, unitSymbol) {
    const canvas = document.getElementById('weatherTrendChart');
    if (!canvas || !chartData) return;

    if (weatherChartInstance) {
        weatherChartInstance.destroy();
    }

    let dataset = [];

    if (activeChartMetric === 'temp') {
        dataset = [{
            label: `Temperature (${unitSymbol})`,
            data: chartData.temperatures,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointBackgroundColor: '#2563eb',
            pointRadius: 4
        }];
    } else if (activeChartMetric === 'rain') {
        dataset = [{
            label: 'Rain Probability (%)',
            data: chartData.rain_pop,
            borderColor: '#06b6d4',
            backgroundColor: 'rgba(6, 182, 212, 0.35)',
            type: 'bar',
            borderRadius: 6
        }];
    } else {
        dataset = [
            {
                label: 'Humidity (%)',
                data: chartData.humidity,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.08)',
                fill: true,
                tension: 0.3,
                borderWidth: 2
            },
            {
                label: 'Wind Speed',
                data: chartData.wind,
                borderColor: '#f59e0b',
                backgroundColor: 'transparent',
                tension: 0.3,
                borderWidth: 2,
                borderDash: [5, 5]
            }
        ];
    }

    weatherChartInstance = new Chart(canvas, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: dataset
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: { font: { family: 'Plus Jakarta Sans', size: 12 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    padding: 10,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(226, 232, 240, 0.6)' },
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 11 } }
                }
            }
        }
    });
}

function setFavoriteState(isFav) {
    const icon = document.getElementById('favIcon');
    const text = document.getElementById('favText');
    if (!icon || !text) return;

    if (isFav) {
        icon.className = 'fa-solid fa-heart me-1 text-danger';
        text.textContent = 'Saved';
    } else {
        icon.className = 'fa-regular fa-heart me-1';
        text.textContent = 'Save City';
    }
}

function showAlert(message, type = 'info') {
    const container = document.getElementById('alertsContainer');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show shadow-sm d-flex align-items-center gap-2 mb-2`;
    alertDiv.innerHTML = `
        <i class="fa-solid fa-circle-info"></i>
        <div>${message}</div>
        <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
    `;
    container.prepend(alertDiv);

    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 200);
    }, 6000);
}
