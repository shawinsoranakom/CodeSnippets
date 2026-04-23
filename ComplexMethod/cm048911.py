def _expected_result_for_thread(self, channel):
        common_data = {
            "has_mail_thread": True,
            "id": channel.id,
            "model": "discuss.channel",
            "module_icon": "/mail/static/description/icon.png",
            "rating_avg": 0.0,
            "rating_count": 0,
        }
        if channel == self.channel_general:
            return {**common_data, "display_name": "general"}
        if channel == self.channel_channel_public_1:
            return {**common_data, "display_name": "public channel 1"}
        if channel == self.channel_channel_public_2:
            return {**common_data, "display_name": "public channel 2"}
        if channel == self.channel_channel_group_1:
            return {**common_data, "display_name": "group restricted channel 1"}
        if channel == self.channel_channel_group_2:
            return {**common_data, "display_name": "group restricted channel 2"}
        if channel == self.channel_livechat_1:
            return {**common_data, "display_name": "test1 Ernest Employee"}
        if channel == self.channel_livechat_2:
            return {**common_data, "display_name": "Visitor Ernest Employee"}
        return {}