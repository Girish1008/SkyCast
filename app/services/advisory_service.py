class AdvisoryService:
    """
    AI/Rule-Based Smart Recommendation Engine.
    Generates personalized suggestions for clothing, outdoor activities, travel safety, and health.
    """

    @classmethod
    def generate_recommendations(cls, weather: dict) -> dict:
        temp = weather.get('temp', 20)
        units = weather.get('units', 'metric')
        temp_c = temp if units == 'metric' else (temp - 32) * 5/9
        humidity = weather.get('humidity', 50)
        wind_speed = weather.get('wind_speed', 3)
        wind_m_s = wind_speed if units == 'metric' else wind_speed * 0.44704
        cond = weather.get('condition', '').lower()

        # 1. Clothing Suggestions
        clothing = []
        gear = []

        if temp_c < 5:
            clothing.append("Heavy thermal jacket, wool sweater, and thermal inner wear")
            clothing.append("Warm trousers, wool gloves, and a beanie/scarf")
            gear.append("Insulated thermal flask")
        elif 5 <= temp_c < 15:
            clothing.append("Medium jacket, cardigan, or hoodie with denim/chinos")
            clothing.append("Comfortable sneakers or closed boots")
        elif 15 <= temp_c < 25:
            clothing.append("Light cotton shirt, t-shirt, light jacket or windbreaker")
            clothing.append("Breathable pants or jeans")
        else:  # >= 25°C
            clothing.append("Loose, light-colored breathable linen or moisture-wicking fabrics")
            clothing.append("Shorts or light cotton trousers")
            gear.append("UV-blocking sunglasses & Sunscreen SPF 50+")

        if 'rain' in cond or 'drizzle' in cond or 'thunderstorm' in cond:
            clothing.append("Waterproof hooded rain jacket or poncho and water-resistant footwear")
            gear.append("Sturdy windproof umbrella")

        if temp_c >= 28 or (temp_c >= 24 and humidity >= 70):
            gear.append("Water bottle for constant electrolyte hydration")

        # 2. Outdoor Activities Suitability
        activity_score = 5
        activity_status = "Excellent"
        reasons = []

        if 'thunderstorm' in cond:
            activity_score = 1
            activity_status = "Hazardous"
            reasons.append("Severe lightning and thunderstorm risks outdoors")
        elif 'rain' in cond:
            activity_score = 2
            activity_status = "Poor"
            reasons.append("Slippery surfaces and continuous wet precipitation")
        elif wind_m_s >= 14:
            activity_score = 2
            activity_status = "Challenging"
            reasons.append("Strong wind gusts")
        elif temp_c >= 36:
            activity_score = 2
            activity_status = "Caution: Heat Risk"
            reasons.append("High risk of dehydration and heat stress")
        elif temp_c <= -2:
            activity_score = 2
            activity_status = "Very Cold"
            reasons.append("Risk of hypothermia and frost")
        elif 18 <= temp_c <= 26 and humidity <= 65 and 'clear' in cond:
            activity_score = 5
            activity_status = "Ideal Conditions"
            reasons.append("Pleasant temperature and clear skies")
        else:
            activity_score = 4
            activity_status = "Good"
            reasons.append("Favorable weather for most outdoor hobbies")

        activities = {
            'Running & Jogging': "Recommended early morning or dusk" if temp_c > 26 else ("Not recommended due to rain" if 'rain' in cond else "Optimal"),
            'Cycling': "Caution on wet roads" if 'rain' in cond else ("Careful with crosswinds" if wind_m_s > 10 else "Great weather for cycling"),
            'Hiking & Parks': "Pack rainproof gear" if 'rain' in cond else "Wonderful for nature walks",
            'Indoor Alternative': "Visit an art gallery, gym, or read at a cafe" if activity_score <= 2 else "Optional"
        }

        # 3. Driving and Travel Conditions
        driving_index = "Good"
        driving_notes = "Normal road safety standards apply."
        if 'thunderstorm' in cond or 'rain' in cond or wind_m_s >= 15:
            driving_index = "Caution Required"
            driving_notes = "Maintain extra braking distance, turn on headlights, and beware of slick asphalt."
        elif weather.get('visibility', 10) < 3:
            driving_index = "Low Visibility Warning"
            driving_notes = "Fog or dense precipitation; use fog lamps and decrease driving speed."

        # 4. Health & Wellness Tips
        health_tips = []
        if temp_c > 30:
            health_tips.append("Drink at least 2.5 - 3 liters of water today to prevent heat exhaustion.")
        if humidity > 80:
            health_tips.append("High humidity levels might feel stuffy; ensure good indoor air circulation.")
        elif humidity < 30:
            health_tips.append("Dry air detected; consider moisturizing skin and hydrating regularly.")
        if temp_c < 10:
            health_tips.append("Sudden temperature drops can trigger seasonal flu; keep your chest and neck covered.")
        if not health_tips:
            health_tips.append("Air quality and ambient conditions are within comfortable wellness parameters.")

        return {
            'clothing': clothing,
            'gear': gear,
            'activity_score': activity_score,
            'activity_status': activity_status,
            'activity_notes': reasons[0] if reasons else "Pleasant ambient weather.",
            'activities': activities,
            'driving_index': driving_index,
            'driving_notes': driving_notes,
            'health_tips': health_tips
        }
