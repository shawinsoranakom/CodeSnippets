def do_GET(self):

        def respond(payload=b'<html><video src="/vid.mp4" /></html>',
                    payload_type='text/html; charset=utf-8',
                    payload_encoding=None,
                    resp_code=200):
            self.send_response(resp_code)
            self.send_header('Content-Type', payload_type)
            if payload_encoding:
                self.send_header('Content-Encoding', payload_encoding)
            self.send_header('Content-Length', str(len(payload)))  # required for persistent connections
            self.end_headers()
            self.wfile.write(payload)

        def gzip_compress(p):
            buf = io.BytesIO()
            with contextlib.closing(gzip.GzipFile(fileobj=buf, mode='wb')) as f:
                f.write(p)
            return buf.getvalue()

        if self.path == '/video.html':
            respond()
        elif self.path == '/vid.mp4':
            respond(b'\x00\x00\x00\x00\x20\x66\x74[video]', 'video/mp4')
        elif self.path == '/302':
            if sys.version_info[0] == 3:
                # XXX: Python 3 http server does not allow non-ASCII header values
                self.send_response(404)
                self.end_headers()
                return

            new_url = self._test_url('中文.html')
            self.send_response(302)
            self.send_header(b'Location', new_url.encode('utf-8'))
            self.end_headers()
        elif self.path == '/%E4%B8%AD%E6%96%87.html':
            respond()
        elif self.path == '/%c7%9f':
            respond()
        elif self.path == '/redirect_dotsegments':
            self.send_response(301)
            # redirect to /headers but with dot segments before
            self.send_header('Location', '/a/b/./../../headers')
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path.startswith('/redirect_'):
            self._redirect()
        elif self.path.startswith('/method'):
            self._method('GET')
        elif self.path.startswith('/headers'):
            self._headers()
        elif self.path.startswith('/308-to-headers'):
            self.send_response(308)
            self.send_header('Location', '/headers')
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path == '/trailing_garbage':
            payload = b'<html><video src="/vid.mp4" /></html>'
            compressed = gzip_compress(payload) + b'trailing garbage'
            respond(compressed, payload_encoding='gzip')
        elif self.path == '/302-non-ascii-redirect':
            new_url = self._test_url('中文.html')
            # actually respond with permanent redirect
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
                    payload = gzip_compress(payload)
                elif encoding == 'deflate':
                    payload = zlib.compress(payload)
                elif encoding == 'unsupported':
                    payload = b'raw'
                    break
                else:
                    self._status(415)
                    return
            respond(payload, payload_encoding=encodings)

        else:
            self._status(404)