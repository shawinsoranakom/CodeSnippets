def test_default_configuration(self, temp_persistence_dir):
        """Test default configuration values."""
        service = DbSessionInjector(persistence_dir=temp_persistence_dir)

        assert service.persistence_dir == temp_persistence_dir
        assert service.host is None
        assert service.port == 5432  # Default from env var processing
        assert service.name == 'openhands'  # Default from env var processing
        assert service.user == 'postgres'  # Default from env var processing
        assert (
            service.password.get_secret_value() == 'postgres'
        )  # Default from env var processing
        assert service.echo is False
        assert service.pool_size == 25
        assert service.max_overflow == 10
        assert service.gcp_db_instance is None
        assert service.gcp_project is None
        assert service.gcp_region is None