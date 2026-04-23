def __call__(self, chain: HandlerChain, context: RequestContext, response: Response):
        if not context.operation:
            return

        if context.service_response:
            return

        if exception := context.service_exception:
            if isinstance(exception, ServiceException):
                if not hasattr(exception, "code"):
                    # FIXME: we should set the exception attributes in the scaffold when we generate the exceptions.
                    #  this is a workaround for now, since we are not doing that yet, and the attributes may be unset.
                    self._set_exception_attributes(context.operation, exception)
                return
            # this shouldn't happen, but we'll log a warning anyway
            else:
                LOG.warning("Cannot parse exception %s", context.service_exception)
                return

        if response.content_length is None or context.operation.has_event_stream_output:
            # cannot/should not parse streaming responses
            context.service_response = {}
            return

        # in this case we need to parse the raw response
        parsed = parse_response(
            context.operation, context.protocol, response, include_response_metadata=False
        )
        if service_exception := parse_service_exception(response, parsed):
            context.service_exception = service_exception
        else:
            context.service_response = parsed