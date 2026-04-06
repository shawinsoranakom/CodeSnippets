def do_request() -> tuple[int, bytes]:
        response = client.post(path, json=json)
        return response.status_code, response.content