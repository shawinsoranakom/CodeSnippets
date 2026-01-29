async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pure ASGI middleware implementation for better performance than BaseHTTPMiddleware."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract path from scope
        path = scope["path"]

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Add security headers to the response
                headers = dict(message.get("headers", []))

                # Add general security headers (HTTP spec requires proper capitalization)
                headers[b"X-Content-Type-Options"] = b"nosniff"
                headers[b"X-Frame-Options"] = b"DENY"
                headers[b"X-XSS-Protection"] = b"1; mode=block"
                headers[b"Referrer-Policy"] = b"strict-origin-when-cross-origin"

                # Add noindex header for shared execution pages
                if "/public/shared" in path:
                    headers[b"X-Robots-Tag"] = b"noindex, nofollow"

                # Default: Disable caching for all endpoints
                # Only allow caching for explicitly permitted paths
                if not self.is_cacheable_path(path):
                    headers[b"Cache-Control"] = (
                        b"no-store, no-cache, must-revalidate, private"
                    )
                    headers[b"Pragma"] = b"no-cache"
                    headers[b"Expires"] = b"0"

                # Convert headers back to list format
                message["headers"] = list(headers.items())

            await send(message)

        await self.app(scope, receive, send_wrapper)
