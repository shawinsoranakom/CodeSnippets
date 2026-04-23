async def create_async_generator(
            cls,
            model: str,
            messages: Messages,
            stream: bool = True,
            proxy: str = None,
            api_key: str = None,
            connector: BaseConnector = None,
            scope: str = "GIGACHAT_API_PERS",
            update_interval: float = 0,
            **kwargs
    ) -> AsyncResult:
        global access_token, token_expires_at
        model = cls.get_model(model)
        if not api_key:
            raise MissingAuthError('Missing "api_key"')

        # Create certificate file in cookies directory
        cookies_dir = Path(get_cookies_dir())
        cert_file = cookies_dir / 'russian_trusted_root_ca.crt'

        # Write certificate if it doesn't exist
        if not cert_file.exists():
            cert_file.write_text(RUSSIAN_CA_CERT)

        if has_ssl and connector is None:
            ssl_context = ssl.create_default_context(cafile=str(cert_file))
            connector = TCPConnector(ssl_context=ssl_context)

        async with ClientSession(connector=get_connector(connector, proxy)) as session:
            if token_expires_at - int(time.time() * 1000) < 60000:
                async with session.post(url="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                                        headers={"Authorization": f"Bearer {api_key}",
                                                 "RqUID": str(uuid.uuid4()),
                                                 "Content-Type": "application/x-www-form-urlencoded"},
                                        data={"scope": scope}) as response:
                    await raise_for_status(response)
                    data = await response.json()
                access_token = data['access_token']
                token_expires_at = data['expires_at']

            async with session.post(url="https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                                    headers={"Authorization": f"Bearer {access_token}"},
                                    json={
                                        "model": model,
                                        "messages": messages,
                                        "stream": stream,
                                        "update_interval": update_interval,
                                        **kwargs
                                    }) as response:
                await raise_for_status(response)

                async for line in response.content:
                    if not stream:
                        yield json.loads(line.decode("utf-8"))['choices'][0]['message']['content']
                        return

                    if line and line.startswith(b"data:"):
                        line = line[6:-1]  # remove "data: " prefix and "\n" suffix
                        if line.strip() == b"[DONE]":
                            return
                        else:
                            msg = json.loads(line.decode("utf-8"))['choices'][0]
                            content = msg['delta']['content']

                            if content:
                                yield content

                            if 'finish_reason' in msg:
                                return