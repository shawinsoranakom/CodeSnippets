def update_state(self, state_hash):
        """Update all the state properties with the passed in dictionary."""
        if "player_state" in state_hash:
            self.player_state = state_hash.get("player_state", None)

        if "name" in state_hash:
            name = state_hash.get("name", "")
            self.device_name = f"{name} AirTunes Speaker".strip()

        if "kind" in state_hash:
            self.kind = state_hash.get("kind", None)

        if "active" in state_hash:
            self.active = state_hash.get("active", None)

        if "selected" in state_hash:
            self.selected = state_hash.get("selected", None)

        if "sound_volume" in state_hash:
            self.volume = state_hash.get("sound_volume", 0)

        if "supports_audio" in state_hash:
            self.supports_audio = state_hash.get("supports_audio", None)

        if "supports_video" in state_hash:
            self.supports_video = state_hash.get("supports_video", None)