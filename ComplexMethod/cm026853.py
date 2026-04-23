def _convert_info_condition(self, info: str) -> str:
        """Return the condition corresponding to the weather info."""
        info = info.lower()
        if WEATHER_INFO_RAIN in info:
            return ATTR_CONDITION_RAINY
        if WEATHER_INFO_SNOW in info and WEATHER_INFO_RAIN in info:
            return ATTR_CONDITION_SNOWY_RAINY
        if WEATHER_INFO_SNOW in info:
            return ATTR_CONDITION_SNOWY
        if WEATHER_INFO_FOG in info or WEATHER_INFO_MIST in info:
            return ATTR_CONDITION_FOG
        if WEATHER_INFO_WIND in info and WEATHER_INFO_CLOUD in info:
            return ATTR_CONDITION_WINDY_VARIANT
        if WEATHER_INFO_WIND in info:
            return ATTR_CONDITION_WINDY
        if WEATHER_INFO_THUNDERSTORM in info and WEATHER_INFO_ISOLATED not in info:
            return ATTR_CONDITION_LIGHTNING_RAINY
        if (
            (
                WEATHER_INFO_RAIN in info
                or WEATHER_INFO_SHOWER in info
                or WEATHER_INFO_THUNDERSTORM in info
            )
            and WEATHER_INFO_HEAVY in info
            and WEATHER_INFO_SUNNY not in info
            and WEATHER_INFO_FINE not in info
            and WEATHER_INFO_AT_TIMES_AT_FIRST not in info
        ):
            return ATTR_CONDITION_POURING
        if (
            (
                WEATHER_INFO_RAIN in info
                or WEATHER_INFO_SHOWER in info
                or WEATHER_INFO_THUNDERSTORM in info
            )
            and WEATHER_INFO_SUNNY not in info
            and WEATHER_INFO_FINE not in info
        ):
            return ATTR_CONDITION_RAINY
        if (WEATHER_INFO_CLOUD in info or WEATHER_INFO_OVERCAST in info) and not (
            WEATHER_INFO_INTERVAL in info or WEATHER_INFO_PERIOD in info
        ):
            return ATTR_CONDITION_CLOUDY
        if (WEATHER_INFO_SUNNY in info) and (
            WEATHER_INFO_INTERVAL in info or WEATHER_INFO_PERIOD in info
        ):
            return ATTR_CONDITION_PARTLYCLOUDY
        if (
            WEATHER_INFO_SUNNY in info or WEATHER_INFO_FINE in info
        ) and WEATHER_INFO_SHOWER not in info:
            return ATTR_CONDITION_SUNNY
        return ATTR_CONDITION_PARTLYCLOUDY