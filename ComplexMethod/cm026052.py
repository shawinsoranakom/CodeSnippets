def handle_event(self, response):
        """Handle responses from the speakers."""
        data = response.get("data") or {}
        if response["msg"] == "EQ_VIEW_INFO":
            self._update_equalisers(data)
        elif response["msg"] == "SPK_LIST_VIEW_INFO":
            if "i_vol" in data:
                self._volume = data["i_vol"]
            if "i_vol_min" in data:
                self._volume_min = data["i_vol_min"]
            if "i_vol_max" in data:
                self._volume_max = data["i_vol_max"]
            if "b_mute" in data:
                self._mute = data["b_mute"]
            if "i_curr_func" in data:
                self._function = data["i_curr_func"]
            if "b_powerstatus" in data:
                self._device_on = data["b_powerstatus"]
                if data["b_powerstatus"]:
                    self._attr_state = MediaPlayerState.ON
                else:
                    self._attr_state = MediaPlayerState.OFF
        elif response["msg"] == "FUNC_VIEW_INFO":
            if "i_curr_func" in data:
                self._function = data["i_curr_func"]
            if "ai_func_list" in data:
                self._functions = data["ai_func_list"]
        elif response["msg"] == "SETTING_VIEW_INFO":
            if "i_rear_min" in data:
                self._rear_volume_min = data["i_rear_min"]
            if "i_rear_max" in data:
                self._rear_volume_max = data["i_rear_max"]
            if "i_rear_level" in data:
                self._rear_volume = data["i_rear_level"]
            if "i_woofer_min" in data:
                self._woofer_volume_min = data["i_woofer_min"]
            if "i_woofer_max" in data:
                self._woofer_volume_max = data["i_woofer_max"]
            if "i_woofer_level" in data:
                self._woofer_volume = data["i_woofer_level"]
            if "i_curr_eq" in data:
                self._equaliser = data["i_curr_eq"]
            if "s_user_name" in data:
                self._attr_name = data["s_user_name"]
        elif response["msg"] == "PLAY_INFO":
            self._update_playinfo(data)

        self.schedule_update_ha_state()