def do_GET(self):
            from urllib.parse import parse_qs

            # Parse the path
            parsed = urlparse(self.path)

            # Serve the test page for root and callback
            if parsed.path in ["/", "/callback"]:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_content.encode())

            # Proxy API calls to backend (avoids CORS issues)
            # Supports both /proxy/api/* and /proxy/external-api/*
            elif parsed.path.startswith("/proxy/"):
                try:
                    # Extract the API path and token from query params
                    api_path = parsed.path[len("/proxy") :]
                    query_params = parse_qs(parsed.query)
                    token = query_params.get("token", [None])[0]

                    headers = {}
                    if token:
                        headers["Authorization"] = f"Bearer {token}"

                    req = Request(
                        f"{backend_url}{api_path}",
                        headers=headers,
                        method="GET",
                    )

                    with urlopen(req) as response:
                        response_body = response.read()
                        self.send_response(response.status)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(response_body)

                except Exception as e:
                    error_msg = str(e)
                    status_code = 500
                    if hasattr(e, "code"):
                        status_code = e.code  # type: ignore
                    if hasattr(e, "read"):
                        try:
                            error_body = e.read().decode()  # type: ignore
                            error_data = json_module.loads(error_body)
                            error_msg = error_data.get("detail", error_msg)
                        except Exception:
                            pass

                    self.send_response(status_code)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json_module.dumps({"detail": error_msg}).encode())

            else:
                self.send_response(404)
                self.end_headers()