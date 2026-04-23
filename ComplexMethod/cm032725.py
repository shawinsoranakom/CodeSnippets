async def async_chat_streamly(self, system, history, gen_conf, images=None, **kwargs):
        gen_conf = self._clean_conf(gen_conf)
        total_tokens = 0
        try:
            response = self.async_client.messages.create(
                model=self.model_name,
                messages=self._form_history(system, history, images),
                system=system,
                stream=True,
                **gen_conf,
            )
            think = False
            async for res in response:
                if res.type == "content_block_delta":
                    if res.delta.type == "thinking_delta" and res.delta.thinking:
                        if not think:
                            yield "<think>"
                            think = True
                        yield res.delta.thinking
                        total_tokens += num_tokens_from_string(res.delta.thinking)
                    elif think:
                        yield "</think>"
                    else:
                        yield res.delta.text
                        total_tokens += num_tokens_from_string(res.delta.text)
        except Exception as e:
            yield "\n**ERROR**: " + str(e)

        yield total_tokens