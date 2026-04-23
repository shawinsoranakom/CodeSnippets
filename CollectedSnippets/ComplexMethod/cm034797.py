async def streaming():
                    try:
                        async for chunk in response:
                            if isinstance(chunk, BaseConversation):
                                if config.conversation_id is not None and config.provider is not None:
                                    if config.conversation_id not in self.conversations:
                                        self.conversations[config.conversation_id] = {}
                                    self.conversations[config.conversation_id][config.provider] = chunk
                            else:
                                yield f"data: {chunk.model_dump_json() if hasattr(chunk, 'model_dump_json') else chunk.json()}\n\n"
                    except GeneratorExit:
                        pass
                    except Exception as e:
                        logger.exception(e)
                        yield f'data: {format_exception(e, config)}\n\n'
                    yield "data: [DONE]\n\n"