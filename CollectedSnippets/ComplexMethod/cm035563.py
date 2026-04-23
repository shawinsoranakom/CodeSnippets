def test_jwe_backwards_compatibility_with_python_jose_tokens(self, jwt_service):
        """Test that JWE tokens created with python-jose can be decrypted with jwcrypto.

        This test ensures backwards compatibility during the migration from python-jose
        to jwcrypto. These tokens were generated using python-jose with the same key
        derivation used by jwt_service (SHA256 of the secret key).

        The tokens use:
        - Algorithm: dir (direct encryption)
        - Encryption: A256GCM
        - Key: SHA256 hash of 'test_secret_key_1' (matches key1 fixture)
        """
        # Token with simple payload: {"user_id": "123", "role": "admin", "iat": 1704067200}
        simple_token = (
            'eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwia2lkIjoia2V5MSJ9'
            '..NJs9xezbNx3va7Q1.I7FvCODEX_cnrB7qmAVkxFaNET89ZoEVo9Enp33plE7jeBJObPGPzWLjEg-khlzeggyUa_7u'
            '.TmGNAVzMIIl4dbMB5NfyGg'
        )

        # Token with complex nested payload
        complex_token = (
            'eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwia2lkIjoia2V5MSJ9'
            '..trjTZoGEg_mBSE3r.-o5RbtSnF_cacNnWQ_z4LGzA1FKfo5OFetjJzvgEAOe0z7DOvzAURIkUwhgKGWM55HEqRGrH'
            'KrIvdNi8-VeWA0p0-bbX0rHHSK4qN1pRfMAbm7ftQ5tl-UMnG52z5D8aFZM6JRGz5loynqo__lx2onSb87t84tcpvK'
            'yteyu7vnoqKxDUw0iK-TwQGg12jz0a1PgHneCqdE8.wzWMxLkkPv7O3dbkrrNraw'
        )

        # Token with unicode characters in payload
        unicode_token = (
            'eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwia2lkIjoia2V5MSJ9'
            '..y5Ez0HSrowxdufK5.Egv1ApEVRg-O5RN8GKj1K-1jLA9DZVQrx2vc7a0lkZkW4FQ3PtEMym3UXClIpbIiO4zLrd1U'
            'cq3sBaBqAhand4hYXte1GvANBqtn59mAoyEZz_w1dFQJQfUYvXrphf2ZjrRC6GuVILsUncK1Kyttc_E0hfnaet6vOU'
            '3MCrGueR1LQNhg7SZo8eXyEDoPfqgXBEpM9OInMg.AiGz8aLdIPUZ__OkezpkmA'
        )

        # Test simple token decryption
        simple_decrypted = jwt_service.decrypt_jwe_token(simple_token)
        assert simple_decrypted['user_id'] == '123'
        assert simple_decrypted['role'] == 'admin'
        assert simple_decrypted['iat'] == 1704067200

        # Test complex token decryption with nested structures
        complex_decrypted = jwt_service.decrypt_jwe_token(complex_token)
        assert complex_decrypted['user_id'] == 'user123'
        assert complex_decrypted['metadata']['permissions'] == [
            'read',
            'write',
            'admin',
        ]
        assert complex_decrypted['metadata']['settings']['theme'] == 'dark'
        assert complex_decrypted['metadata']['settings']['notifications'] is True
        assert complex_decrypted['iat'] == 1704067200

        # Test unicode token decryption
        unicode_decrypted = jwt_service.decrypt_jwe_token(unicode_token)
        assert unicode_decrypted['user_name'] == 'José María'
        assert unicode_decrypted['description'] == 'Testing with émojis 🚀'
        assert unicode_decrypted['chinese'] == '你好世界'
        assert unicode_decrypted['iat'] == 1704067200