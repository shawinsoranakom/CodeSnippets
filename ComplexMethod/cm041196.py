def _log(self, context: RequestContext, response: Response):
        aws_logger = self.aws_logger
        http_logger = self.http_logger
        if context.is_internal_call:
            aws_logger = self.internal_aws_logger
            http_logger = self.internal_http_logger
        if context.operation:
            # log an AWS response
            if context.service_exception:
                aws_logger.info(
                    "AWS %s.%s => %d (%s)",
                    context.service.service_name,
                    context.operation.name,
                    response.status_code,
                    context.service_exception.code,
                    extra={
                        # context
                        "account_id": context.account_id,
                        "region": context.region,
                        # request
                        "input_type": context.operation.input_shape.name
                        if context.operation.input_shape
                        else "Request",
                        "input": context.service_request,
                        "request_headers": dict(context.request.headers),
                        # response
                        "output_type": context.service_exception.code,
                        "output": context.service_exception.message,
                        "response_headers": dict(response.headers),
                    },
                )
            else:
                aws_logger.info(
                    "AWS %s.%s => %s",
                    context.service.service_name,
                    context.operation.name,
                    response.status_code,
                    extra={
                        # context
                        "account_id": context.account_id,
                        "region": context.region,
                        # request
                        "input_type": context.operation.input_shape.name
                        if context.operation.input_shape
                        else "Request",
                        "input": context.service_request,
                        "request_headers": dict(context.request.headers),
                        # response
                        "output_type": context.operation.output_shape.name
                        if context.operation.output_shape
                        else "Response",
                        "output": context.service_response,
                        "response_headers": dict(response.headers),
                    },
                )
        else:
            # log any other HTTP response
            http_logger.info(
                "%s %s => %d",
                context.request.method,
                context.request.path,
                response.status_code,
                extra={
                    # request
                    "input_type": "Request",
                    "input": restore_payload(context.request),
                    "request_headers": dict(context.request.headers),
                    # response
                    "output_type": "Response",
                    "output": "StreamingBody(unknown)" if response.is_streamed else response.data,
                    "response_headers": dict(response.headers),
                },
            )