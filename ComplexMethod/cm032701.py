async def _async_chat_streamly(self, history, gen_conf, **kwargs):
        logging.info("[HISTORY STREAMLY]" + json.dumps(history, ensure_ascii=False, indent=4))
        reasoning_start = False

        request_kwargs = {"model": self.model_name, "messages": history, "stream": True, **gen_conf}
        stop = kwargs.get("stop")
        if stop:
            request_kwargs["stop"] = stop

        response = await self.async_client.chat.completions.create(**request_kwargs)
        async for resp in response:
            if not resp.choices:
                continue
            if not resp.choices[0].delta.content:
                resp.choices[0].delta.content = ""
            _reasoning = getattr(resp.choices[0].delta, "reasoning_content", None) or getattr(resp.choices[0].delta, "reasoning", None)
            if kwargs.get("with_reasoning", True) and _reasoning:
                ans = ""
                if not reasoning_start:
                    reasoning_start = True
                    ans = "<think>"
                ans += _reasoning + "</think>"
            else:
                reasoning_start = False
                ans = resp.choices[0].delta.content
            tol = total_token_count_from_response(resp)
            if not tol:
                tol = num_tokens_from_string(resp.choices[0].delta.content)

            finish_reason = resp.choices[0].finish_reason if hasattr(resp.choices[0], "finish_reason") else ""
            if finish_reason == "length":
                if is_chinese(ans):
                    ans += LENGTH_NOTIFICATION_CN
                else:
                    ans += LENGTH_NOTIFICATION_EN
            yield ans, tol