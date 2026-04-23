async def _get_sound_modes_info(self):
        """Get available sound modes and the active one."""
        for settings in await self._dev.get_sound_settings():
            if settings.target == "soundField":
                break
        else:
            return None, {}

        if isinstance(settings, Setting):
            settings = [settings]

        sound_modes = {}
        active_sound_mode = None
        for setting in settings:
            cur = setting.currentValue
            for opt in setting.candidate:
                if not opt.isAvailable:
                    continue
                if opt.value == cur:
                    active_sound_mode = opt.value
                sound_modes[opt.value] = opt

        _LOGGER.debug("Got sound modes: %s", sound_modes)
        _LOGGER.debug("Active sound mode: %s", active_sound_mode)

        return active_sound_mode, sound_modes