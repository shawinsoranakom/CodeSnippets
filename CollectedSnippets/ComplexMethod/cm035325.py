def _select_llm(self, messages: list[Message]) -> str:
        """Select LLM based on multimodal content and token limits."""
        route_to_primary = False

        # Check for multimodal content in messages
        for message in messages:
            if message.contains_image:
                logger.info(
                    'Multimodal content detected in messages. Routing to the primary model.'
                )
                route_to_primary = True

        if not route_to_primary and self.max_token_exceeded:
            route_to_primary = True

        # Check if `messages` exceeds context window of the secondary model
        # Assuming the secondary model has a lower context window limit compared to the primary model
        secondary_llm = self.available_llms.get(self.SECONDARY_MODEL_CONFIG_NAME)
        if secondary_llm and (
            secondary_llm.config.max_input_tokens
            and secondary_llm.get_token_count(messages)
            > secondary_llm.config.max_input_tokens
        ):
            logger.warning(
                f"Messages having {secondary_llm.get_token_count(messages)} tokens, exceed secondary model's max input tokens ({secondary_llm.config.max_input_tokens} tokens). "
                'Routing to the primary model.'
            )
            self.max_token_exceeded = True
            route_to_primary = True

        if route_to_primary:
            logger.info('Routing to the primary model...')
            return 'primary'
        else:
            logger.info('Routing to the secondary model...')
            return self.SECONDARY_MODEL_CONFIG_NAME