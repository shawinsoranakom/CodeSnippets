def get_random_platform(self, device_type, os_type, device_brand):
        """Helper method to get random platform based on constraints"""
        platforms = (
            self.desktop_platforms
            if device_type == "desktop"
            else self.mobile_platforms
            if device_type == "mobile"
            else {**self.desktop_platforms, **self.mobile_platforms}
        )

        if os_type:
            for platform_group in [self.desktop_platforms, self.mobile_platforms]:
                if os_type in platform_group:
                    platforms = {os_type: platform_group[os_type]}
                    break

        os_key = random.choice(list(platforms.keys()))
        if device_brand and device_brand in platforms[os_key]:
            return platforms[os_key][device_brand]
        return random.choice(list(platforms[os_key].values()))