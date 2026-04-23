def get_api_response(endpoint, api_token=None, params=None, verbosity=0):
    if api_token is None:
        api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/json",
    }
    endpoint = endpoint.strip("/")
    url = f"https://rest.api.transifex.com/{endpoint}"
    if verbosity > 2:
        print(f"\n>>> GET {url=} {params=}")
    response = requests.get(url, headers=headers, params=params)
    if verbosity > 2:
        print(f">>>> GET {response=}\n")
    response.raise_for_status()
    return response.json()["data"]