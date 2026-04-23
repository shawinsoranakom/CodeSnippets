async def test_multiple_device_authentication(self, mock_store, mock_api_key_class):
        """Test that multiple devices can authenticate simultaneously."""
        # Mock API key store with async create_api_key
        mock_api_key_store = MagicMock()
        mock_api_key_store.create_api_key = AsyncMock()
        mock_api_key_class.get_instance.return_value = mock_api_key_store

        # Simulate two different devices
        device1_code = 'ABC12345'
        device2_code = 'XYZ67890'
        user_id = 'user-123'

        # Mock device codes
        mock_device1 = MagicMock()
        mock_device1.is_pending.return_value = True
        mock_device2 = MagicMock()
        mock_device2.is_pending.return_value = True

        # Configure mock store to return appropriate device for each user_code
        async def get_by_user_code_side_effect(user_code):
            if user_code == device1_code:
                return mock_device1
            elif user_code == device2_code:
                return mock_device2
            return None

        mock_store.get_by_user_code = AsyncMock(
            side_effect=get_by_user_code_side_effect
        )
        mock_store.authorize_device_code = AsyncMock(return_value=True)

        # Authenticate first device
        result1 = await device_verification_authenticated(
            user_code=device1_code, user_id=user_id
        )

        # Authenticate second device
        result2 = await device_verification_authenticated(
            user_code=device2_code, user_id=user_id
        )

        # Both should succeed
        assert isinstance(result1, JSONResponse)
        assert result1.status_code == 200
        assert isinstance(result2, JSONResponse)
        assert result2.status_code == 200

        # Should create two separate API keys with different names
        assert mock_api_key_store.create_api_key.call_count == 2

        # Check that each device got a unique API key name
        call_args_list = mock_api_key_store.create_api_key.call_args_list
        device1_name = call_args_list[0][1]['name']
        device2_name = call_args_list[1][1]['name']

        assert device1_name == f'Device Link Access Key ({device1_code})'
        assert device2_name == f'Device Link Access Key ({device2_code})'
        assert device1_name != device2_name  # Ensure they're different

        # Should NOT delete any existing API keys
        mock_api_key_store.delete_api_key_by_name.assert_not_called()