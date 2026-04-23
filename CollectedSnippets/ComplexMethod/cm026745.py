def supported(domain, features, device_class, _):
        """Test if state is supported."""
        if domain == fan.DOMAIN and features & FanEntityFeature.PRESET_MODE:
            return True

        if domain == input_select.DOMAIN:
            return True

        if domain == select.DOMAIN:
            return True

        if domain == humidifier.DOMAIN and features & HumidifierEntityFeature.MODES:
            return True

        if domain == light.DOMAIN and features & LightEntityFeature.EFFECT:
            return True

        if (
            domain == water_heater.DOMAIN
            and features & WaterHeaterEntityFeature.OPERATION_MODE
        ):
            return True

        if domain != media_player.DOMAIN:
            return False

        return features & MediaPlayerEntityFeature.SELECT_SOUND_MODE