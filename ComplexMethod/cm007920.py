def do_GET(self):
        if self.path == '/video.html':
            payload = b'<html><video src="/vid.mp4" /></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == '/vid.mp4':
            payload = b'\x00\x00\x00\x00\x20\x66\x74[video]'
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == '/%E4%B8%AD%E6%96%87.html':
            payload = b'<html><video src="/vid.mp4" /></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == '/%c7%9f':
            payload = b'<html><video src="/vid.mp4" /></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path.startswith('/redirect_loop'):
            self.send_response(301)
            self.send_header('Location', self.path)
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path == '/redirect_dotsegments':
            self.send_response(301)
            # redirect to /headers but with dot segments before
            self.send_header('Location', '/a/b/./../../headers')
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path == '/redirect_dotsegments_absolute':
            self.send_response(301)
            # redirect to /headers but with dot segments before - absolute url
            self.send_header('Location', f'http://127.0.0.1:{http_server_port(self.server)}/a/b/./../../headers')
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path.startswith('/redirect_'):
            self._redirect()
        elif self.path.startswith('/method'):
            self._method('GET', str(self.headers).encode())
        elif self.path.startswith('/headers'):
            self._headers()
        elif self.path.startswith('/308-to-headers'):
            self.send_response(308)
            # redirect to "localhost" for testing cookie redirection handling
            self.send_header('Location', f'http://localhost:{self.connection.getsockname()[1]}/headers')
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path == '/trailing_garbage':
            payload = b'<html><video src="/vid.mp4" /></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Encoding', 'gzip')
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='wb') as f:
                f.write(payload)
            compressed = buf.getvalue() + b'trailing garbage'
            self.send_header('Content-Length', str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        elif self.path == '/302-non-ascii-redirect':
            new_url = f'http://127.0.0.1:{http_server_port(self.server)}/中文.html'
            self.send_response(301)
            self.send_header('Location', new_url)
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path == '/content-encoding':
            encodings = self.headers.get('ytdl-encoding', '')
            payload = b'<html><video src="/vid.mp4" /></html>'
            for encoding in filter(None, (e.strip() for e in encodings.split(','))):
                if encoding == 'br' and brotli:
                    payload = brotli.compress(payload)
                elif encoding == 'gzip':
                    payload = gzip.compress(payload, mtime=0)
                elif encoding == 'deflate':
                    payload = zlib.compress(payload)
                elif encoding == 'unsupported':
                    payload = b'raw'
                    break
                else:
                    self._status(415)
                    return
            self.send_response(200)
            self.send_header('Content-Encoding', encodings)
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path.startswith('/gen_'):
            payload = b'<html></html>'
            self.send_response(int(self.path[len('/gen_'):]))
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path.startswith('/incompleteread'):
            payload = b'<html></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', '234234')
            self.end_headers()
            self.wfile.write(payload)
            self.finish()
        elif self.path.startswith('/timeout_'):
            time.sleep(int(self.path[len('/timeout_'):]))
            self._headers()
        elif self.path == '/source_address':
            payload = str(self.client_address[0]).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            self.finish()
        elif self.path == '/get_cookie':
            self.send_response(200)
            self.send_header('Set-Cookie', 'test=ytdlp; path=/')
            self.end_headers()
            self.finish()
        else:
            self._status(404)