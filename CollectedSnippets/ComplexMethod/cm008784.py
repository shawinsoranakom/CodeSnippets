def communicate_ws(reconnect):
            # Support --load-info-json as if it is a reconnect attempt
            if reconnect or not isinstance(ws_extractor, WebSocketResponse):
                ws = self.ydl.urlopen(Request(
                    ws_url, headers={'Origin': 'https://live.nicovideo.jp'}))
                if self.ydl.params.get('verbose', False):
                    self.write_debug('Sending startWatching request')
                ws.send(json.dumps({
                    'data': {
                        'reconnect': True,
                        'room': {
                            'commentable': True,
                            'protocol': 'webSocket',
                        },
                        'stream': {
                            'accessRightMethod': 'single_cookie',
                            'chasePlay': False,
                            'latency': 'high',
                            'protocol': 'hls',
                            'quality': quality,
                        },
                    },
                    'type': 'startWatching',
                }))
            else:
                ws = ws_extractor
            with ws:
                while True:
                    recv = ws.recv()
                    if not recv:
                        continue
                    data = json.loads(recv)
                    if not data or not isinstance(data, dict):
                        continue
                    if data.get('type') == 'ping':
                        ws.send(r'{"type":"pong"}')
                        ws.send(r'{"type":"keepSeat"}')
                    elif data.get('type') == 'disconnect':
                        self.write_debug(data)
                        return True
                    elif data.get('type') == 'error':
                        self.write_debug(data)
                        message = traverse_obj(data, ('body', 'code', {str_or_none}), default=recv)
                        return DownloadError(message)
                    elif self.ydl.params.get('verbose', False):
                        self.write_debug(f'Server response: {truncate_string(recv, 100)}')