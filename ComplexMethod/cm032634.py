def test_parse_id_token_success_and_error(monkeypatch):
    _, oidc_module = _load_auth_modules(monkeypatch)
    client = _make_client(monkeypatch, oidc_module)

    monkeypatch.setattr(oidc_module.jwt, "get_unverified_header", lambda _token: {})

    seen = {}

    class _JwkClient(_DummyJwkClient):
        def __init__(self, jwks_uri):
            super().__init__(jwks_uri)
            seen["jwks_uri"] = jwks_uri

        def get_signing_key_from_jwt(self, id_token):
            seen["id_token"] = id_token
            return super().get_signing_key_from_jwt(id_token)

    monkeypatch.setattr(oidc_module.jwt, "PyJWKClient", _JwkClient)

    def _decode(id_token, key, algorithms, audience, issuer):
        seen.update(
            {
                "decode_id_token": id_token,
                "decode_key": key,
                "algorithms": algorithms,
                "audience": audience,
                "issuer": issuer,
            }
        )
        return {"sub": "user-1", "email": "id@example.com"}

    monkeypatch.setattr(oidc_module.jwt, "decode", _decode)
    parsed = client.parse_id_token("id-token-1")

    assert parsed["sub"] == "user-1"
    assert seen["jwks_uri"] == "https://issuer.example/jwks"
    assert seen["decode_key"] == "dummy-signing-key"
    assert seen["algorithms"] == ["RS256"]
    assert seen["audience"] == "client-1"
    assert seen["issuer"] == "https://issuer.example"

    def _raise_decode(*_args, **_kwargs):
        raise RuntimeError("decode boom")

    monkeypatch.setattr(oidc_module.jwt, "decode", _raise_decode)
    with pytest.raises(ValueError) as exc_info:
        client.parse_id_token("id-token-2")
    assert str(exc_info.value) == "Error parsing ID Token: decode boom"