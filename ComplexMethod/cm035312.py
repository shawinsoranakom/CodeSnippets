def _completion_cost(self, response: Any) -> float:
        """Calculate completion cost and update metrics with running total.

        Calculate the cost of a completion response based on the model. Local models are treated as free.
        Add the current cost into total cost in metrics.

        Args:
            response: A response from a model invocation.

        Returns:
            number: The cost of the response.
        """
        if not self.cost_metric_supported:
            return 0.0

        extra_kwargs = {}
        if (
            self.config.input_cost_per_token is not None
            and self.config.output_cost_per_token is not None
        ):
            cost_per_token = CostPerToken(
                input_cost_per_token=self.config.input_cost_per_token,
                output_cost_per_token=self.config.output_cost_per_token,
            )
            logger.debug(f'Using custom cost per token: {cost_per_token}')
            extra_kwargs['custom_cost_per_token'] = cost_per_token

        # try directly get response_cost from response
        _hidden_params = getattr(response, '_hidden_params', {})
        cost = _hidden_params.get('additional_headers', {}).get(
            'llm_provider-x-litellm-response-cost', None
        )
        if cost is not None:
            cost = float(cost)
            logger.debug(f'Got response_cost from response: {cost}')

        try:
            if cost is None:
                try:
                    cost = litellm_completion_cost(
                        completion_response=response, **extra_kwargs
                    )
                except Exception as e:
                    logger.debug(f'Error getting cost from litellm: {e}')

            if cost is None:
                _model_name = '/'.join(self.config.model.split('/')[1:])
                cost = litellm_completion_cost(
                    completion_response=response, model=_model_name, **extra_kwargs
                )
                logger.debug(
                    f'Using fallback model name {_model_name} to get cost: {cost}'
                )
            self.metrics.add_cost(float(cost))
            return float(cost)
        except Exception:
            self.cost_metric_supported = False
            logger.debug('Cost calculation not supported for this model.')
        return 0.0