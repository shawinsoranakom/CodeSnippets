def is_app_server_alive():
    try:
        r = requests.get("http://localhost:3000/", timeout=3)
        return r.status_code == requests.codes.ok
    except:
        return False