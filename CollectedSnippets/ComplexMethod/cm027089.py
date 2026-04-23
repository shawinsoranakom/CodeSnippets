async def _get_latest_video_url(self):
        """Retrieve the latest video file from the customized Yi FTP server."""
        ftp = Client()
        try:
            await ftp.connect(self.host)
            await ftp.login(self.user, self.passwd)
        except (ConnectionRefusedError, StatusCodeError) as err:
            raise PlatformNotReady(err) from err

        try:
            await ftp.change_directory(self.path)
            dirs = []
            for path, attrs in await ftp.list():
                if attrs["type"] == "dir" and "." not in str(path):
                    dirs.append(path)
            latest_dir = dirs[-1]
            await ftp.change_directory(latest_dir)

            videos = []
            for path, _ in await ftp.list():
                videos.append(path)
            if not videos:
                _LOGGER.info('Video folder "%s" empty; delaying', latest_dir)
                return None

            await ftp.quit()
            self._attr_is_on = True
            return (
                f"ftp://{self.user}:{self.passwd}@{self.host}:"
                f"{self.port}{self.path}/{latest_dir}/{videos[-1]}"
            )
        except (ConnectionRefusedError, StatusCodeError) as err:
            _LOGGER.error("Error while fetching video: %s", err)
            self._attr_is_on = False
            return None