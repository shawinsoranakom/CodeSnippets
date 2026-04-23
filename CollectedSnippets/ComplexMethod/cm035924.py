def test_override_removes_oss_route_and_adds_saas_route(self):
        """override_users_me_endpoint should remove OSS route and add SAAS route."""
        from fastapi import FastAPI
        from server.routes.users_v1 import override_users_me_endpoint

        # Create a minimal app with a mock OSS route
        app = FastAPI()

        @app.get('/api/v1/users/me')
        def mock_oss_endpoint():
            return {'source': 'oss'}

        # Verify OSS route exists
        oss_routes = [
            r for r in app.routes if hasattr(r, 'path') and r.path == '/api/v1/users/me'
        ]
        assert len(oss_routes) == 1
        assert oss_routes[0].endpoint.__name__ == 'mock_oss_endpoint'

        # Apply the override
        override_users_me_endpoint(app)

        # Verify SAAS route exists and OSS route is gone
        saas_routes = [
            r for r in app.routes if hasattr(r, 'path') and r.path == '/api/v1/users/me'
        ]
        assert len(saas_routes) == 1
        assert saas_routes[0].endpoint.__name__ == 'get_current_user_saas'