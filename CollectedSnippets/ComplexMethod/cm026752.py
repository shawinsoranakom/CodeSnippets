def _air_quality_description_for_aqi(self, aqi: float | None) -> str:
        if aqi is None or aqi < 0:
            return "unknown"
        if aqi <= 50:
            return "healthy"
        if aqi <= 100:
            return "moderate"
        if aqi <= 150:
            return "unhealthy for sensitive groups"
        if aqi <= 200:
            return "unhealthy"
        if aqi <= 300:
            return "very unhealthy"

        return "hazardous"