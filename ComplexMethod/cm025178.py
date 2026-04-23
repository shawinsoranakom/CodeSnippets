async def async_validate_login(self, username: str, password: str) -> None:
        """Validate a username and password."""
        env = {"username": username, "password": password}
        try:
            process = await asyncio.create_subprocess_exec(
                self.config[CONF_COMMAND],
                *self.config[CONF_ARGS],
                env=env,
                stdout=asyncio.subprocess.PIPE if self.config[CONF_META] else None,
                close_fds=False,  # required for posix_spawn
            )
            stdout, _ = await process.communicate()
        except OSError as err:
            # happens when command doesn't exist or permission is denied
            _LOGGER.error("Error while authenticating %r: %s", username, err)
            raise InvalidAuthError from err

        if process.returncode != 0:
            _LOGGER.error(
                "User %r failed to authenticate, command exited with code %d",
                username,
                process.returncode,
            )
            raise InvalidAuthError

        if self.config[CONF_META]:
            meta: dict[str, str] = {}
            for _line in stdout.splitlines():
                try:
                    line = _line.decode().lstrip()
                except ValueError:
                    # malformed line
                    continue
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key in self.ALLOWED_META_KEYS:
                    meta[key] = value
            self._user_meta[username] = meta