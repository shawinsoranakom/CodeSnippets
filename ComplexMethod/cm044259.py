def command(
        self,
        func: Callable[P, OBBject] | None = None,
        **kwargs,
    ) -> Callable | None:
        """Command decorator for routes."""
        if func is None:
            return lambda f: self.command(f, **kwargs)

        api_router = self._api_router
        model = kwargs.pop("model", "")
        no_validate = kwargs.pop("no_validate", None)
        openapi_extra = kwargs.get("openapi_extra") or {}
        kwargs["openapi_extra"] = openapi_extra

        if widget_config := kwargs.pop("widget_config", None):
            openapi_extra["widget_config"] = widget_config

        if mcp_config := kwargs.pop("mcp_config", None):
            openapi_extra["mcp_config"] = mcp_config

        if no_validate is True:
            func.__annotations__["return"] = None

        if func := SignatureInspector.complete(func, model):
            kwargs["response_model_exclude_unset"] = True
            openapi_extra["model"] = model
            openapi_extra["examples"] = filter_list(
                examples=kwargs.pop("examples", []),
                providers=ProviderInterface().available_providers,
            )
            openapi_extra["no_validate"] = no_validate
            kwargs["operation_id"] = kwargs.get(
                "operation_id", SignatureInspector.get_operation_id(func)
            )
            kwargs["path"] = kwargs.get("path", f"/{func.__name__}")
            kwargs["endpoint"] = func
            kwargs["methods"] = kwargs.get("methods", ["GET"])
            kwargs["response_model"] = (
                kwargs.get(
                    "response_model",
                    func.__annotations__["return"],  # type: ignore
                )
                if not no_validate
                else func.__annotations__["return"]
            )
            kwargs["response_model_by_alias"] = kwargs.get(
                "response_model_by_alias", False
            )
            kwargs["description"] = SignatureInspector.get_description(func)
            kwargs["responses"] = kwargs.get(
                "responses",
                {
                    204: {
                        "description": "Empty response",
                    },
                    400: {
                        "model": OpenBBErrorResponse,
                        "description": "No Results Found",
                    },
                    404: {"description": "Not found"},
                    500: {
                        "model": OpenBBErrorResponse,
                        "description": "Internal Error",
                    },
                    502: {
                        "model": OpenBBErrorResponse,
                        "description": "Unauthorized",
                    },
                },
            )

            # For custom deprecation
            if kwargs.get("deprecated", False):
                deprecation: OpenBBDeprecationWarning = kwargs.pop("deprecation")

                kwargs["summary"] = DeprecationSummary(
                    deprecation.long_message, deprecation
                )

            kwargs["openapi_extra"] = openapi_extra

            api_router.add_api_route(**kwargs)

        return func