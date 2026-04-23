def __validate_external_request_features(self, request: PoTokenRequest):
        if self._SUPPORTED_EXTERNAL_REQUEST_FEATURES is None:
            return

        if request.request_proxy:
            scheme = urllib.parse.urlparse(request.request_proxy).scheme
            if scheme.lower() not in self._supported_proxy_schemes:
                raise PoTokenProviderRejectedRequest(
                    f'External requests by "{self.PROVIDER_NAME}" provider do not '
                    f'support proxy scheme "{scheme}". Supported proxy schemes: '
                    f'{", ".join(self._supported_proxy_schemes) or "none"}')

        if (
            request.request_source_address
            and ExternalRequestFeature.SOURCE_ADDRESS not in self._SUPPORTED_EXTERNAL_REQUEST_FEATURES
        ):
            raise PoTokenProviderRejectedRequest(
                f'External requests by "{self.PROVIDER_NAME}" provider '
                f'do not support setting source address')

        if (
            not request.request_verify_tls
            and ExternalRequestFeature.DISABLE_TLS_VERIFICATION not in self._SUPPORTED_EXTERNAL_REQUEST_FEATURES
        ):
            raise PoTokenProviderRejectedRequest(
                f'External requests by "{self.PROVIDER_NAME}" provider '
                f'do not support ignoring TLS certificate failures')