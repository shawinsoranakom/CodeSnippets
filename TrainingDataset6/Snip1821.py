def _get_last_n(n):
    with socket.socket(socket.AF_UNIX) as client:
        client.connect(_get_socket_path())
        request = json.dumps({
            "type": "list",
            "count": n,
        }) + '\n'
        client.sendall(request.encode('utf-8'))
        response = client.makefile().readline()
        return json.loads(response)['commands']