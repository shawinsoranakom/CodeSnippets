def open(self, *args, **kwargs) -> Optional[Awaitable[None]]:
        # Extract user info from the X-Streamlit-User header
        is_public_cloud_app = False

        try:
            header_content = self.request.headers["X-Streamlit-User"]
            payload = base64.b64decode(header_content)
            user_obj = json.loads(payload)
            email = user_obj["email"]
            is_public_cloud_app = user_obj["isPublicCloudApp"]
        except (KeyError, binascii.Error, json.decoder.JSONDecodeError):
            email = "test@localhost.com"

        user_info: Dict[str, Optional[str]] = dict()
        if is_public_cloud_app:
            user_info["email"] = None
        else:
            user_info["email"] = email

        self._session_id = self._runtime.create_session(self, user_info)
        return None