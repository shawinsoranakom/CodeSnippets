async def test_update_build_config_auth_jwt(self, component_class):
        """Test update_build_config with JWT authentication."""
        component = component_class()
        build_config = {
            "username": {"required": False, "show": False},
            "password": {"required": False, "show": False},
            "jwt_token": {"required": False, "show": False},
            "bearer_token": {"required": False, "show": False},
            "bearer_prefix": {"required": False, "show": False},
            "jwt_header": {"required": False, "show": False},
        }

        updated_config = await component.update_build_config(build_config, "jwt", "auth_mode")

        # Verify JWT fields are visible and required
        assert updated_config["jwt_token"]["show"] is True
        assert updated_config["jwt_token"]["required"] is True
        assert updated_config["jwt_header"]["show"] is True
        assert updated_config["jwt_header"]["required"] is True
        assert updated_config["bearer_prefix"]["show"] is True
        assert updated_config["bearer_prefix"]["required"] is False
        # Basic auth fields should be hidden
        assert updated_config["username"]["show"] is False
        assert updated_config["password"]["show"] is False