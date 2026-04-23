async def async_chat(self, system, history, gen_conf, **kwargs):
        hist = list(history) if history else []
        if system:
            if not hist or hist[0].get("role") != "system":
                hist.insert(0, {"role": "system", "content": system})

        logging.info("[HISTORY]" + json.dumps(hist, ensure_ascii=False, indent=2))
        gen_conf = self._clean_conf(gen_conf)
        _, kwargs = _apply_model_family_policies(
            self.model_name,
            backend="litellm",
            provider=self.provider,
            request_kwargs=kwargs,
        )

        completion_args = self._construct_completion_args(history=hist, stream=False, tools=False, **{**gen_conf, **kwargs})

        for attempt in range(self.max_retries + 1):
            try:
                response = await litellm.acompletion(
                    **completion_args,
                    drop_params=True,
                    timeout=self.timeout,
                )

                if any([not response.choices, not response.choices[0].message, not response.choices[0].message.content]):
                    return "", 0
                ans = response.choices[0].message.content.strip()
                if response.choices[0].finish_reason == "length":
                    ans = self._length_stop(ans)

                return ans, total_token_count_from_response(response)
            except Exception as e:
                e = await self._exceptions_async(e, attempt)
                if e:
                    return e, 0

        assert False, "Shouldn't be here."