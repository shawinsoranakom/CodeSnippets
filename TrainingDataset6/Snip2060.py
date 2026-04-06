def do_request() -> tuple[int, bytes]:
        response = client.get(path)
        return response.status_code, response.content