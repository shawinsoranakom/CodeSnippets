def _get_next_app_info(self):
        if self._APP_INFO_POOL is None:
            defaults = {
                key: self._configuration_arg(key, [default], ie_key=TikTokIE)[0]
                for key, default in self._APP_INFO_DEFAULTS.items()
                if key != 'iid'
            }
            self._APP_INFO_POOL = [
                {**defaults, **dict(
                    (k, v) for k, v in zip(self._APP_INFO_DEFAULTS, app_info.split('/'), strict=False) if v
                )} for app_info in self._KNOWN_APP_INFO
            ]

        if not self._APP_INFO_POOL:
            return False

        self._APP_INFO = self._APP_INFO_POOL.pop(0)

        app_name = self._APP_INFO['app_name']
        version = self._APP_INFO['manifest_app_version']
        if app_name == 'musical_ly':
            package = f'com.zhiliaoapp.musically/{version}'
        else:  # trill, aweme
            package = f'com.ss.android.ugc.{app_name}/{version}'
        self._APP_USER_AGENT = f'{package} (Linux; U; Android 13; en_US; Pixel 7; Build/TD1A.220804.031; Cronet/58.0.2991.0)'

        return True