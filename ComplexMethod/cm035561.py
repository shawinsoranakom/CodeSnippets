def test_jws_token_round_trip_default_key(self, jwt_service):
        """Test JWS token creation and verification round trip with default key."""
        payload = {'user_id': '123', 'role': 'admin', 'custom_data': {'foo': 'bar'}}

        # Create token
        token = jwt_service.create_jws_token(payload)

        # Verify token
        decoded_payload = jwt_service.verify_jws_token(token)

        # Check that original payload is preserved
        assert decoded_payload['user_id'] == payload['user_id']
        assert decoded_payload['role'] == payload['role']
        assert decoded_payload['custom_data'] == payload['custom_data']

        # Check that standard JWT claims are added
        assert 'iat' in decoded_payload
        assert 'exp' in decoded_payload
        # JWT library converts datetime to Unix timestamps
        assert isinstance(decoded_payload['iat'], int)
        assert isinstance(decoded_payload['exp'], int)