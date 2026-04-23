def _proxy(*args, **kwargs) -> WerkzeugResponse:
            # extract request from function invocation (decorator can be used for methods as well as for functions).
            if len(args) > 0 and isinstance(args[0], WerkzeugRequest):
                # function
                request = args[0]
            elif len(args) > 1 and isinstance(args[1], WerkzeugRequest):
                # method (arg[0] == self)
                request = args[1]
            elif "request" in kwargs:
                request = kwargs["request"]
            else:
                raise ValueError(f"could not find Request in signature of function {fn}")

            # TODO: we have no context here
            # TODO: maybe try to get the request ID from the headers first before generating a new one
            request_id = gen_amzn_requestid()

            try:
                response = fn(*args, **kwargs)

                if isinstance(response, WerkzeugResponse):
                    return response

                return serializer.serialize_to_response(
                    response, operation_model, request.headers, request_id
                )

            except ServiceException as e:
                return serializer.serialize_error_to_response(
                    e, operation_model, request.headers, request_id
                )
            except Exception as e:
                return serializer.serialize_error_to_response(
                    CommonServiceException(
                        "InternalError", f"An internal error occurred: {e}", status_code=500
                    ),
                    operation_model,
                    request.headers,
                    request_id,
                )