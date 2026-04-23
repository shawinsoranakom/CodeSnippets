def get_latest_video_url(self, host):
        """Retrieve the latest video file from the Xiaomi Camera FTP server."""

        ftp = FTP(host)
        try:
            ftp.login(self.user, self.passwd)
        except error_perm as exc:
            _LOGGER.error("Camera login failed: %s", exc)
            return False

        try:
            ftp.cwd(self.path)
        except error_perm as exc:
            _LOGGER.error("Unable to find path: %s - %s", self.path, exc)
            return False

        dirs = [d for d in ftp.nlst() if "." not in d]
        if not dirs:
            _LOGGER.warning("There don't appear to be any folders")
            return False

        first_dir = latest_dir = dirs[-1]
        try:
            ftp.cwd(first_dir)
        except error_perm as exc:
            _LOGGER.error("Unable to find path: %s - %s", first_dir, exc)
            return False

        if self._model == MODEL_XIAOFANG:
            dirs = [d for d in ftp.nlst() if "." not in d]
            if not dirs:
                _LOGGER.warning("There don't appear to be any uploaded videos")
                return False

            latest_dir = dirs[-1]
            ftp.cwd(latest_dir)

        videos = [v for v in ftp.nlst() if ".tmp" not in v]
        if not videos:
            _LOGGER.debug('Video folder "%s" is empty; delaying', latest_dir)
            return False

        if self._model == MODEL_XIAOFANG:
            video = videos[-2]
        else:
            video = videos[-1]

        return f"ftp://{self.user}:{self.passwd}@{host}:{self.port}{ftp.pwd()}/{video}"