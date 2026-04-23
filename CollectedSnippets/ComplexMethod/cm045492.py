async def authenticate(self, websocket: WebSocket) -> bool:
        """
        Authenticate a WebSocket connection.
        Returns True if authenticated, False otherwise.
        """
        if self.auth_manager.config.type == "none":
            return True

        try:
            # Extract token from query params or cookies
            token = None
            if "token" in websocket.query_params:
                token = websocket.query_params["token"]
            elif "authorization" in websocket.headers:
                auth_header = websocket.headers["authorization"]
                if auth_header.startswith("Bearer "):
                    token = auth_header.replace("Bearer ", "")

            if not token:
                logger.warning("No token found for WebSocket connection")
                return False

            # Validate token
            valid = self.auth_manager.is_valid_token(token)
            if not valid:
                logger.warning("Invalid token for WebSocket connection")
                return False

            return True

        except Exception as e:
            logger.error(f"WebSocket auth error: {str(e)}")
            return False