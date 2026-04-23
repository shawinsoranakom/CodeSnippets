def do_trace_call(
        self, fn: Callable, chain: HandlerChain, context: RequestContext, response: Response
    ):
        """
        Wraps the function call with the tracing functionality and records a HandlerTrace.

        The method determines changes made by the request handler to specific aspects of the request.
        Changes made to the request context and the response headers/status by the request handler are then
        examined, and appropriate actions are added to the `actions` list of the trace.

        :param fn: which is the function to be traced, which is the request/response/exception handler
        :param chain: the handler chain
        :param context: the request context
        :param response: the response object
        """
        then = time.perf_counter()

        actions = []

        prev_context = dict(context.__dict__)
        prev_stopped = chain.stopped
        prev_request_identity = id(context.request)
        prev_terminated = chain.terminated
        prev_request_headers = context.request.headers.copy()
        prev_response_headers = response.headers.copy()
        prev_response_status = response.status_code

        # add patches to log invocations or certain functions
        patches = Patches(
            [
                Patch.function(
                    context.request.get_data,
                    _log_method_call("request.get_data", actions),
                ),
                Patch.function(
                    context.request._load_form_data,
                    _log_method_call("request._load_form_data", actions),
                ),
                Patch.function(
                    response.get_data,
                    _log_method_call("response.get_data", actions),
                ),
            ]
        )
        patches.apply()

        try:
            return fn()
        finally:
            now = time.perf_counter()
            # determine some basic things the handler changed in the context
            patches.undo()

            # chain
            if chain.stopped and not prev_stopped:
                actions.append(Action("stop chain"))
            if chain.terminated and not prev_terminated:
                actions.append(Action("terminate chain"))

            # detect when attributes are set in the request contex
            context_args = dict(context.__dict__)
            context_args.pop("request", None)  # request is handled separately

            for k, v in context_args.items():
                if not v:
                    continue
                if prev_context.get(k):
                    # TODO: we could introduce "ModifyAttributeAction(k,v)" with an additional check
                    #  ``if v != prev_context.get(k)``
                    continue
                actions.append(SetAttributeAction(k, v))

            # request
            if id(context.request) != prev_request_identity:
                actions.append(Action("replaced request object"))

            # response
            if response.status_code != prev_response_status:
                actions.append(SetAttributeAction("response stats_code", response.status_code))
            if context.request.headers != prev_request_headers:
                actions.append(
                    ModifyHeadersAction(
                        "modify request headers",
                        prev_request_headers,
                        context.request.headers.copy(),
                    )
                )
            if response.headers != prev_response_headers:
                actions.append(
                    ModifyHeadersAction(
                        "modify response headers", prev_response_headers, response.headers.copy()
                    )
                )

            self.trace = HandlerTrace(
                handler=self.delegate, duration_ms=(now - then) * 1000, actions=actions
            )