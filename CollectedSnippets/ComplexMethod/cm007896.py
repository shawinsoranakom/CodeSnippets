def websocket_handler(websocket):
    for message in websocket:
        if isinstance(message, bytes):
            if message == b'bytes':
                return websocket.send('2')
        elif isinstance(message, str):
            if message == 'headers':
                return websocket.send(json.dumps(dict(websocket.request.headers.raw_items())))
            elif message == 'path':
                return websocket.send(websocket.request.path)
            elif message == 'source_address':
                return websocket.send(websocket.remote_address[0])
            elif message == 'str':
                return websocket.send('1')
        return websocket.send(message)