def test_postgres_connection_with_host(self, postgres_db_session_injector):
        """Test PostgreSQL connection when host is defined."""
        with patch(
            'openhands.app_server.services.db_session_injector.create_engine'
        ) as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            engine = postgres_db_session_injector.get_db_engine()

            assert engine == mock_engine
            # Check that create_engine was called with the right parameters
            assert mock_create_engine.call_count == 1
            call_args = mock_create_engine.call_args

            # Verify the URL contains the expected components
            url_str = str(call_args[0][0])
            assert 'postgresql+pg8000://' in url_str
            assert 'test_user' in url_str
            # Password may be masked in URL string representation
            assert 'test_password' in url_str or '***' in url_str
            assert 'localhost:5432' in url_str
            assert 'test_db' in url_str

            # Verify other parameters
            assert call_args[1]['pool_size'] == 25
            assert call_args[1]['max_overflow'] == 10
            assert call_args[1]['pool_pre_ping']