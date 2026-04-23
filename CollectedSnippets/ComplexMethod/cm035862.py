async def get_idp_tokens_from_keycloak(
        self,
        access_token: str,
        idp: ProviderType,
    ) -> dict[str, str | int]:
        async with httpx.AsyncClient(
            verify=httpx_verify_option(), timeout=IDP_HTTP_TIMEOUT
        ) as client:
            base_url = KEYCLOAK_SERVER_URL_EXT if self.external else KEYCLOAK_SERVER_URL
            url = f'{base_url}/realms/{KEYCLOAK_REALM_NAME}/broker/{idp.value}/token'
            headers = {
                'Authorization': f'Bearer {access_token}',
            }

            data: dict[str, str | int] = {}
            response = await client.get(url, headers=headers)
            content_str = response.content.decode('utf-8')
            if (
                f'Identity Provider [{idp.value}] does not support this operation.'
                in content_str
            ):
                return data
            response.raise_for_status()
            try:
                # Try parsing as JSON
                data = json.loads(response.text)
            except json.JSONDecodeError:
                # If it's not JSON, try parsing as a URL-encoded string
                parsed = parse_qs(response.text)
                # Convert lists to strings and specific keys to integers
                data = {
                    key: int(value[0])
                    if key
                    in {'expires_in', 'refresh_token_expires_in', 'refresh_expires_in'}
                    else value[0]
                    for key, value in parsed.items()
                }

            current_time = int(time.time())
            expires_in = int(data.get('expires_in', 0))
            refresh_expires_in = int(
                data.get('refresh_token_expires_in', data.get('refresh_expires_in', 0))
            )
            access_token_expires_at = (
                0 if expires_in == 0 else current_time + expires_in
            )
            refresh_token_expires_at = (
                0 if refresh_expires_in == 0 else current_time + refresh_expires_in
            )

            return {
                'access_token': data['access_token'],
                'refresh_token': data['refresh_token'],
                'access_token_expires_at': access_token_expires_at,
                'refresh_token_expires_at': refresh_token_expires_at,
            }