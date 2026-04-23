def _should_attach(self, request: Request) -> bool:
        if request.method == 'OPTIONS':
            return False
        path = request.url.path

        ignore_paths = (
            '/api/options/config',
            '/api/keycloak/callback',
            '/api/billing/success',
            '/api/billing/cancel',
            '/api/billing/customer-setup-success',
            '/api/billing/stripe-webhook',
            '/api/email/resend',
            '/api/organizations/members/invite/accept',
            '/oauth/device/authorize',
            '/oauth/device/token',
            '/api/v1/web-client/config',
        )
        if path in ignore_paths:
            return False

        # Allow public access to shared conversations and events
        if path.startswith('/api/shared-conversations') or path.startswith(
            '/api/shared-events'
        ):
            return False

        # Webhooks access is controlled using separate API keys
        if path.startswith('/api/v1/webhooks/'):
            return False

        # Service API uses its own authentication (X-Service-API-Key header)
        if path.startswith('/api/service/'):
            return False

        is_mcp = path.startswith('/mcp')
        is_api_route = path.startswith('/api')
        return is_api_route or is_mcp