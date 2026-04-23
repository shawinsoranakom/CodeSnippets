def load_file(
        self,
        url: str | None = None,
        local_path: str | None = None,
        username: str | None = None,
        password: str | None = None,
        auth: str | None = None,
    ) -> BufferedReader | bytes | None:
        """Load image/document/etc from a local path or URL."""
        try:
            if url is not None:
                # Check whether authentication parameters are provided
                if username is not None and password is not None:
                    # Use digest or basic authentication
                    auth_: HTTPDigestAuth | HTTPBasicAuth
                    if auth in (ATTR_IMAGE_AUTH_DIGEST, ATTR_ICON_AUTH_DIGEST):
                        auth_ = HTTPDigestAuth(username, password)
                    else:
                        auth_ = HTTPBasicAuth(username, password)
                    # Load file from URL with authentication
                    req = requests.get(url, auth=auth_, timeout=DEFAULT_TIMEOUT)
                else:
                    # Load file from URL without authentication
                    req = requests.get(url, timeout=DEFAULT_TIMEOUT)
                return req.content

            if local_path is not None:
                # Check whether path is whitelisted in configuration.yaml
                if self.is_allowed_path(local_path):
                    return open(local_path, "rb")
                _LOGGER.warning("'%s' is not secure to load data from!", local_path)
            else:
                _LOGGER.warning("Neither URL nor local path found in params!")

        except OSError as error:
            _LOGGER.error("Can't load from url or local path: %s", error)

        return None