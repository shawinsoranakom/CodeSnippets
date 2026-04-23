def on_request(event: nodriver.cdp.network.RequestWillBeSent, page=None):
                if not hasattr(event, "request"):
                    return
                if event.request.url == start_url or event.request.url.startswith(conversation_url):
                    if cls.request_config.headers is None:
                        cls.request_config.headers = {}
                    for key, value in event.request.headers.items():
                        cls.request_config.headers[key.lower()] = value
                elif event.request.url in (backend_url, backend_anon_url, prepare_url):
                    if "OpenAI-Sentinel-Proof-Token" in event.request.headers:
                        cls.request_config.proof_token = json.loads(base64.b64decode(
                            event.request.headers["OpenAI-Sentinel-Proof-Token"].split("gAAAAAB", 1)[-1].split("~")[
                                0].encode()
                        ).decode())
                    if "OpenAI-Sentinel-Turnstile-Token" in event.request.headers:
                        cls.request_config.turnstile_token = event.request.headers["OpenAI-Sentinel-Turnstile-Token"]
                    if "Authorization" in event.request.headers:
                        cls._api_key = event.request.headers["Authorization"].split()[-1]
                elif event.request.url == arkose_url:
                    cls.request_config.arkose_request = arkReq(
                        arkURL=event.request.url,
                        arkBx=None,
                        arkHeader=event.request.headers,
                        arkBody=event.request.post_data,
                        userAgent=event.request.headers.get("User-Agent")
                    )