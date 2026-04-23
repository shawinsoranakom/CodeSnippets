def do_GET(self):
        if self.path == "/login":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Set-Cookie", "auth_token=valid123; Path=/")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Login</title></head>
<body><h1>Login Page</h1><p>You are now logged in.</p>
<a href="/dashboard">Go to dashboard</a></body></html>""")
            return

        if self.path == "/dashboard":
            cookie = self.headers.get("Cookie", "")
            if "auth_token=valid123" in cookie:
                body = "<h1>Dashboard</h1><p>Welcome, authenticated user!</p>"
            else:
                body = "<h1>Dashboard</h1><p>NOT AUTHENTICATED</p>"
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<!DOCTYPE html><html><head><title>Dashboard</title></head>"
                f"<body>{body}</body></html>".encode()
            )
            return

        if self.path == "/step1":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Step 1</title></head>
<body><h1>Step 1</h1><p>First step complete</p></body></html>""")
            return

        if self.path == "/step2":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Step 2</title></head>
<body><h1>Step 2</h1><p>Second step complete</p></body></html>""")
            return

        if self.path == "/step3":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Step 3</title></head>
<body><h1>Step 3</h1><p>Third step complete</p></body></html>""")
            return

        html = PAGES_HTML.get(self.path)
        if html is None:
            # Fallback for root and unknown paths
            html = PAGES_HTML["/page0"]
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())