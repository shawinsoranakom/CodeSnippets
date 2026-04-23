async def test_secrets_isolation_between_organizations(
        self, mock_get_user, secrets_store, mock_user
    ):
        """Test that secrets from one organization are not deleted when storing
        secrets in another organization. This reproduces a bug where switching
        organizations and creating a secret would delete all secrets from the
        user's personal workspace."""
        org1_id = UUID('a1111111-1111-1111-1111-111111111111')
        org2_id = UUID('b2222222-2222-2222-2222-222222222222')

        # Store secrets in org1 (personal workspace)
        mock_user.current_org_id = org1_id
        mock_get_user.return_value = mock_user
        org1_secrets = Secrets(
            custom_secrets=MappingProxyType(
                {
                    'personal_secret': CustomSecret.from_value(
                        {
                            'secret': 'personal_secret_value',
                            'description': 'My personal secret',
                        }
                    ),
                }
            )
        )
        await secrets_store.store(org1_secrets)

        # Verify org1 secrets are stored
        loaded_org1 = await secrets_store.load()
        assert loaded_org1 is not None
        assert 'personal_secret' in loaded_org1.custom_secrets
        assert (
            loaded_org1.custom_secrets['personal_secret'].secret.get_secret_value()
            == 'personal_secret_value'
        )

        # Switch to org2 and store secrets there
        mock_user.current_org_id = org2_id
        mock_get_user.return_value = mock_user
        org2_secrets = Secrets(
            custom_secrets=MappingProxyType(
                {
                    'org2_secret': CustomSecret.from_value(
                        {'secret': 'org2_secret_value', 'description': 'Org2 secret'}
                    ),
                }
            )
        )
        await secrets_store.store(org2_secrets)

        # Verify org2 secrets are stored
        loaded_org2 = await secrets_store.load()
        assert loaded_org2 is not None
        assert 'org2_secret' in loaded_org2.custom_secrets
        assert (
            loaded_org2.custom_secrets['org2_secret'].secret.get_secret_value()
            == 'org2_secret_value'
        )

        # Switch back to org1 and verify secrets are still there
        mock_user.current_org_id = org1_id
        mock_get_user.return_value = mock_user
        loaded_org1_again = await secrets_store.load()
        assert loaded_org1_again is not None
        assert 'personal_secret' in loaded_org1_again.custom_secrets
        assert (
            loaded_org1_again.custom_secrets[
                'personal_secret'
            ].secret.get_secret_value()
            == 'personal_secret_value'
        )
        # Verify org2 secrets are NOT visible in org1
        assert 'org2_secret' not in loaded_org1_again.custom_secrets