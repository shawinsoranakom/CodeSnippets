async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process each request, authenticating as needed."""
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        if (
            path == "/"
            or path == "/login"
            or path == "/callback"
            or path == "/images"
            or path.startswith("/page-data/")
            or path in self.auth_manager.config.exclude_paths
            or re.match(r"/[^/]+\.(js|css|png|ico|svg|jpg|webmanifest|json)$", path)
            or re.match(r".*\.(js\.map|svg)$", path)
        ):
            return await call_next(request)

        # Skip auth if disabled
        if self.auth_manager.config.type == "none":
            request.state.user = await self.auth_manager.authenticate_request(request)
            return await call_next(request)

        # WebSocket handling (special case)
        if request.url.path.startswith("/api/ws") or request.url.path.startswith("/api/maker"):
            # For WebSockets, we'll add auth in the WebSocket accept handler
            # Just pass through here
            return await call_next(request)

        # Handle authentication for all other requests
        try:
            user = await self.auth_manager.authenticate_request(request)
            # Add user to request state for use in route handlers
            request.state.user = user
            return await call_next(request)

        except AuthException as e:
            # Handle authentication errors
            return Response(
                status_code=HTTP_401_UNAUTHORIZED,
                content=json.dumps({"status": False, "detail": e.detail}),
                media_type="application/json",
                headers=e.headers or {},
            )
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in auth middleware: {str(e)}")
            return Response(
                status_code=HTTP_401_UNAUTHORIZED,
                content=json.dumps({"status": False, "detail": "Authentication failed"}),
                media_type="application/json",
            )