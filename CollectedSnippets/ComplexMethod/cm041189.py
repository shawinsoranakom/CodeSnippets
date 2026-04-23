def __call__(self, chain: HandlerChain, context: RequestContext, response: Response):
        if not config.OPENAPI_VALIDATE_REQUEST:
            return

        hasattr(self, "open_apis") or self._load_specs()
        path = context.request.path

        if path.startswith(f"{INTERNAL_RESOURCE_PATH}/") or path.startswith("/_aws/"):
            for openapi in self.open_apis:
                try:
                    openapi.validate_request(WerkzeugOpenAPIRequest(context.request))
                    # We stop the handler at the first succeeded validation, as the other spec might not even specify
                    #   this path.
                    break
                except RequestValidationError as e:
                    # Note: in this handler we only check validation errors, e.g., wrong body, missing required.
                    response.status_code = 400
                    response.set_json({"error": "Bad Request", "message": str(e)})
                    chain.stop()
                except OpenAPIError:
                    # Other errors can be raised when validating a request against the OpenAPI specification.
                    #   The most common are: ServerNotFound, OperationNotFound, or PathNotFound.
                    #   We explicitly do not check any other error but RequestValidationError ones.
                    #   We shallow the exception to avoid excessive logging (e.g., a lot of ServerNotFound), as the only
                    #   purpose of this handler is to check for request validation errors.
                    pass