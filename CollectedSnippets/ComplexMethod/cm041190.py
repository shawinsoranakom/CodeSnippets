def __call__(self, chain: HandlerChain, context: RequestContext, response: Response):
        # The use of this flag is intended for test only. Eventual errors are due to LocalStack implementation and not
        #   to improper user usage of the endpoints.
        if not config.OPENAPI_VALIDATE_RESPONSE:
            return

        hasattr(self, "open_apis") or self._load_specs()
        path = context.request.path

        if path.startswith(f"{INTERNAL_RESOURCE_PATH}/") or path.startswith("/_aws/"):
            for openapi in self.open_apis:
                try:
                    openapi.validate_response(
                        WerkzeugOpenAPIRequest(context.request),
                        WerkzeugOpenAPIResponse(response),
                    )
                    break
                except ResponseValidationError as exc:
                    LOG.error("Response validation failed for %s: %s", path, exc)
                    response.status_code = 500
                    response.set_json({"error": exc.__class__.__name__, "message": str(exc)})
                    chain.terminate()
                except OpenAPIError:
                    # Same logic from the request validator applies here.
                    pass