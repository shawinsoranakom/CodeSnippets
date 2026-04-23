def _post_completion(self, response: ModelResponse) -> float:
        """Post-process the completion response.

        Logs the cost and usage stats of the completion call.
        """
        try:
            cur_cost = self._completion_cost(response)
        except Exception:
            cur_cost = 0

        stats = ''
        if self.cost_metric_supported:
            # keep track of the cost
            stats = 'Cost: %.2f USD | Accumulated Cost: %.2f USD\n' % (
                cur_cost,
                self.metrics.accumulated_cost,
            )

        # Add latency to stats if available
        if self.metrics.response_latencies:
            latest_latency = self.metrics.response_latencies[-1]
            stats += 'Response Latency: %.3f seconds\n' % latest_latency.latency

        usage: Usage | None = response.get('usage')
        response_id = response.get('id', 'unknown')

        if usage:
            # keep track of the input and output tokens
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            if prompt_tokens:
                stats += 'Input tokens: ' + str(prompt_tokens)

            if completion_tokens:
                stats += (
                    (' | ' if prompt_tokens else '')
                    + 'Output tokens: '
                    + str(completion_tokens)
                    + '\n'
                )

            # read the prompt cache hit, if any
            prompt_tokens_details: PromptTokensDetails = usage.get(
                'prompt_tokens_details'
            )
            cache_hit_tokens = (
                prompt_tokens_details.cached_tokens
                if prompt_tokens_details and prompt_tokens_details.cached_tokens
                else 0
            )
            if cache_hit_tokens:
                stats += 'Input tokens (cache hit): ' + str(cache_hit_tokens) + '\n'

            # For Anthropic, the cache writes have a different cost than regular input tokens
            # but litellm doesn't separate them in the usage stats
            # we can read it from the provider-specific extra field
            model_extra = usage.get('model_extra', {})
            cache_write_tokens = model_extra.get('cache_creation_input_tokens', 0)
            if cache_write_tokens:
                stats += 'Input tokens (cache write): ' + str(cache_write_tokens) + '\n'

            # Get context window from model info
            context_window = 0
            if self.model_info and 'max_input_tokens' in self.model_info:
                context_window = self.model_info['max_input_tokens']
                logger.debug(f'Using context window: {context_window}')

            # Record in metrics
            # We'll treat cache_hit_tokens as "cache read" and cache_write_tokens as "cache write"
            self.metrics.add_token_usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cache_read_tokens=cache_hit_tokens,
                cache_write_tokens=cache_write_tokens,
                context_window=context_window,
                response_id=response_id,
            )

        # log the stats
        if stats:
            logger.debug(stats)

        return cur_cost