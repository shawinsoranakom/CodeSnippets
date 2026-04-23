def test_complex_payload_structures(self, jwt_service):
        """Test JWS and JWE with complex payload structures."""
        complex_payload = {
            'user_id': 'user123',
            'metadata': {
                'permissions': ['read', 'write', 'admin'],
                'settings': {
                    'theme': 'dark',
                    'notifications': True,
                    'nested_array': [
                        {'id': 1, 'name': 'item1'},
                        {'id': 2, 'name': 'item2'},
                    ],
                },
            },
            'timestamps': {
                'created': '2023-01-01T00:00:00Z',
                'last_login': '2023-01-02T12:00:00Z',
            },
            'numbers': [1, 2, 3.14, -5],
            'boolean_flags': {'is_active': True, 'is_verified': False},
        }

        # Test JWS round trip
        jws_token = jwt_service.create_jws_token(complex_payload)
        jws_decoded = jwt_service.verify_jws_token(jws_token)

        # Verify complex structure is preserved
        assert jws_decoded['user_id'] == complex_payload['user_id']
        assert (
            jws_decoded['metadata']['permissions']
            == complex_payload['metadata']['permissions']
        )
        assert (
            jws_decoded['metadata']['settings']['nested_array']
            == complex_payload['metadata']['settings']['nested_array']
        )
        assert jws_decoded['numbers'] == complex_payload['numbers']
        assert jws_decoded['boolean_flags'] == complex_payload['boolean_flags']

        # Test JWE round trip
        jwe_token = jwt_service.create_jwe_token(complex_payload)
        jwe_decrypted = jwt_service.decrypt_jwe_token(jwe_token)

        # Verify complex structure is preserved
        assert jwe_decrypted['user_id'] == complex_payload['user_id']
        assert (
            jwe_decrypted['metadata']['permissions']
            == complex_payload['metadata']['permissions']
        )
        assert (
            jwe_decrypted['metadata']['settings']['nested_array']
            == complex_payload['metadata']['settings']['nested_array']
        )
        assert jwe_decrypted['numbers'] == complex_payload['numbers']
        assert jwe_decrypted['boolean_flags'] == complex_payload['boolean_flags']