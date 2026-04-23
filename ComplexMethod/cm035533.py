def test_environment_variable_processing(self, temp_persistence_dir):
        """Test that environment variables are properly processed."""
        env_vars = {
            'DB_HOST': 'env_host',
            'DB_PORT': '3306',
            'DB_NAME': 'env_db',
            'DB_USER': 'env_user',
            'DB_PASS': 'env_password',
            'GCP_DB_INSTANCE': 'env_instance',
            'GCP_PROJECT': 'env_project',
            'GCP_REGION': 'env_region',
        }

        with patch.dict(os.environ, env_vars):
            service = DbSessionInjector(persistence_dir=temp_persistence_dir)

            assert service.host == 'env_host'
            assert service.port == 3306
            assert service.name == 'env_db'
            assert service.user == 'env_user'
            assert service.password.get_secret_value() == 'env_password'
            assert service.gcp_db_instance == 'env_instance'
            assert service.gcp_project == 'env_project'
            assert service.gcp_region == 'env_region'