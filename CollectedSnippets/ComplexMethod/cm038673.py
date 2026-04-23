async def invocations(raw_request: Request):
        """For SageMaker, routes requests based on the request type."""
        try:
            body = await raw_request.json()
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST.value,
                detail=f"JSON decode error: {e}",
            ) from e

        valid_endpoints = [
            (validator, endpoint)
            for validator, (get_handler, endpoint) in INVOCATION_VALIDATORS
            if get_handler(raw_request) is not None
        ]

        for request_validator, endpoint in valid_endpoints:
            try:
                request = request_validator.validate_python(body)
            except pydantic.ValidationError:
                continue

            return await endpoint(request, raw_request)

        type_names = [
            t.__name__ if isinstance(t := validator._type, type) else str(t)
            for validator, _ in valid_endpoints
        ]
        msg = f"Cannot find suitable handler for request. Expected one of: {type_names}"
        res = base(raw_request).create_error_response(message=msg)
        return JSONResponse(content=res.model_dump(), status_code=res.error.code)