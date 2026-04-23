def set_nstproxy(
        self,
        token: str,
        channel_id: str,
        country: str = "ANY",
        state: str = "",
        city: str = "",
        protocol: str = "http",
        session_duration: int = 10,
    ):
        """
        Fetch a proxy from NSTProxy API and automatically assign it to proxy_config.

        Get your NSTProxy token from: https://app.nstproxy.com/profile

        Args:
            token (str): NSTProxy API token.
            channel_id (str): NSTProxy channel ID.
            country (str, optional): Country code (default: "ANY").
            state (str, optional): State code (default: "").
            city (str, optional): City name (default: "").
            protocol (str, optional): Proxy protocol ("http" or "socks5"). Defaults to "http".
            session_duration (int, optional): Session duration in minutes (0 = rotate each request). Defaults to 10.

        Raises:
            ValueError: If the API response format is invalid.
            PermissionError: If the API returns an error message.
        """

        # --- Validate input early ---
        if not token or not channel_id:
            raise ValueError("[NSTProxy] token and channel_id are required")

        if protocol not in ("http", "socks5"):
            raise ValueError(f"[NSTProxy] Invalid protocol: {protocol}")

        # --- Build NSTProxy API URL ---
        params = {
            "fType": 2,
            "count": 1,
            "channelId": channel_id,
            "country": country,
            "protocol": protocol,
            "sessionDuration": session_duration,
            "token": token,
        }
        if state:
            params["state"] = state
        if city:
            params["city"] = city

        url = "https://api.nstproxy.com/api/v1/generate/apiproxies"

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # --- Handle API error response ---
            if isinstance(data, dict) and data.get("err"):
                raise PermissionError(f"[NSTProxy] API Error: {data.get('msg', 'Unknown error')}")

            if not isinstance(data, list) or not data:
                raise ValueError("[NSTProxy] Invalid API response — expected a non-empty list")

            proxy_info = data[0]

            # --- Apply proxy config ---
            self.proxy_config = ProxyConfig(
                server=f"{protocol}://{proxy_info['ip']}:{proxy_info['port']}",
                username=proxy_info["username"],
                password=proxy_info["password"],
            )

        except Exception as e:
            print(f"[NSTProxy] ❌ Failed to set proxy: {e}")
            raise