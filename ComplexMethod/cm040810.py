def _get_public_parameters(
        self,
        auth_type: ConnectionAuthorizationType,
        auth_parameters: CreateConnectionAuthRequestParameters
        | UpdateConnectionAuthRequestParameters,
    ) -> CreateConnectionAuthRequestParameters:
        """Extract public parameters (without secrets) based on auth type."""
        public_params = {}

        if (
            auth_type == ConnectionAuthorizationType.BASIC
            and "BasicAuthParameters" in auth_parameters
        ):
            public_params["BasicAuthParameters"] = {
                "Username": auth_parameters["BasicAuthParameters"]["Username"]
            }

        elif (
            auth_type == ConnectionAuthorizationType.API_KEY
            and "ApiKeyAuthParameters" in auth_parameters
        ):
            public_params["ApiKeyAuthParameters"] = {
                "ApiKeyName": auth_parameters["ApiKeyAuthParameters"]["ApiKeyName"]
            }

        elif (
            auth_type == ConnectionAuthorizationType.OAUTH_CLIENT_CREDENTIALS
            and "OAuthParameters" in auth_parameters
        ):
            oauth_params = auth_parameters["OAuthParameters"]
            public_params["OAuthParameters"] = {
                "AuthorizationEndpoint": oauth_params["AuthorizationEndpoint"],
                "HttpMethod": oauth_params["HttpMethod"],
                "ClientParameters": {"ClientID": oauth_params["ClientParameters"]["ClientID"]},
            }
            if "OAuthHttpParameters" in oauth_params:
                public_params["OAuthParameters"]["OAuthHttpParameters"] = oauth_params.get(
                    "OAuthHttpParameters"
                )

        if "InvocationHttpParameters" in auth_parameters:
            public_params["InvocationHttpParameters"] = auth_parameters["InvocationHttpParameters"]

        return public_params