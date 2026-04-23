def __call__(self, chain: HandlerChain, context: RequestContext, response: Response):
        if response is None or context.operation is None:
            return
        if config.DISABLE_EVENTS:
            return
        if context.is_internal_call:
            # don't count internal requests
            return

        # this condition will only be true only for the first call, so it makes sense to not acquire the lock every time
        if not self._started:
            with self._mutex:
                if not self._started:
                    self._started = True
                    self.aggregator.start()

        err_type = self._get_err_type(context, response) if response.status_code >= 400 else None
        service_name = context.operation.service_model.service_name
        operation_name = context.operation.name

        self.aggregator.add_request(
            ServiceRequestInfo(
                service_name,
                operation_name,
                response.status_code,
                err_type=err_type,
            )
        )