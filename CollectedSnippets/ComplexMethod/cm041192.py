def create_exception_response(self, exception: Exception, context: RequestContext):
        operation = context.operation
        service_name = context.service.service_name
        error = exception

        if operation and isinstance(exception, NotImplementedError):
            operation_name = operation.name
            exception_message: str | None = exception.args[0] if exception.args else None
            if exception_message:
                message = exception_message
                error = CommonServiceException("InternalFailure", message, status_code=501)
            else:
                catalog = get_aws_catalog()
                if isinstance(exception, PluginNotIncludedInUserLicenseError):
                    # Operation name is provided when a plugin fails to load, although it is not relevant.
                    # In such cases, we should return an error without the operation name
                    service_status = catalog.get_aws_service_status(
                        service_name, operation_name=None
                    )
                else:
                    service_status = catalog.get_aws_service_status(service_name, operation_name)
                error = get_service_availability_exception(
                    service_name, operation_name, service_status
                )
                message = error.message
            LOG.info(message)
            context.service_exception = error
        elif isinstance(exception, self._moto_service_exception):
            # Translate Moto ServiceException to native ServiceException if Moto is available.
            # This allows handler chain to gracefully handles Moto errors when provider handlers invoke Moto methods directly.
            error = CommonServiceException(
                code=exception.code,
                message=exception.message,
            )
        elif isinstance(exception, self._moto_rest_error):
            # Some Moto exceptions (like ones raised by EC2) are of type RESTError.
            error = CommonServiceException(
                code=exception.error_type,
                message=exception.message,
            )

        elif not isinstance(exception, ServiceException):
            if not self.handle_internal_failures:
                return

            if config.INCLUDE_STACK_TRACES_IN_HTTP_RESPONSE:
                message = "".join(
                    traceback.format_exception(
                        type(exception), value=exception, tb=exception.__traceback__
                    )
                )
            else:
                message = str(exception)

            # wrap exception for serialization
            if operation:
                operation_name = operation.name
                msg = f"exception while calling {service_name}.{operation_name}: {message}"
            else:
                # just use any operation for mocking purposes (the parser needs it to populate the default response)
                operation = context.service.operation_model(context.service.operation_names[0])
                msg = f"exception while calling {service_name} with unknown operation: {message}"

            status_code = 501 if config.FAIL_FAST else 500

            error = CommonServiceException(
                "InternalError", msg, status_code=status_code
            ).with_traceback(exception.__traceback__)

        context.service_exception = error

        serializer = create_serializer(context.service, context.protocol)
        return serializer.serialize_error_to_response(
            error, operation, context.request.headers, context.request_id
        )