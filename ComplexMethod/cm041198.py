def update_metric_collection(
        self, chain: HandlerChain, context: RequestContext, response: Response
    ):
        if not config.is_collect_metrics_mode() or not context.service_operation:
            return

        item = self._get_metric_handler_item_for_context(context)

        # parameters might get changed when dispatched to the service - we use the params stored in
        # parameters_after_parse
        parameters = ",".join(item.parameters_after_parse or [])

        response_data = response.data.decode("utf-8") if response.status_code >= 300 else ""
        metric = Metric(
            service=context.service_operation.service,
            operation=context.service_operation.operation,
            headers=context.request.headers,
            parameters=parameters,
            response_code=response.status_code,
            response_data=response_data,
            exception=context.service_exception.__class__.__name__
            if context.service_exception
            else "",
            origin="internal" if context.is_internal_call else "external",
        )
        # refrain from adding duplicates
        if metric not in MetricHandler.metric_data:
            self.append_metric(metric)

        # cleanup
        del self.metrics_handler_items[context]