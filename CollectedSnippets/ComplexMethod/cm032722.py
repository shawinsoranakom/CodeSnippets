async def async_chat_streamly(self, system, history, gen_conf, images=None, **kwargs):
        from rag.llm.chat_model import LENGTH_NOTIFICATION_CN, LENGTH_NOTIFICATION_EN
        from rag.nlp import is_chinese

        if system and history and history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system})
        gen_conf = self._clean_conf(gen_conf)
        ans = ""
        tk_count = 0
        try:
            logging.info(json.dumps(history, ensure_ascii=False, indent=2))
            response = await self.async_client.chat.completions.create(model=self.model_name, messages=self._form_history(system, history, images), stream=True, **gen_conf)
            async for resp in response:
                if not resp.choices[0].delta.content:
                    continue
                delta = resp.choices[0].delta.content
                ans = delta
                if resp.choices[0].finish_reason == "length":
                    if is_chinese(ans):
                        ans += LENGTH_NOTIFICATION_CN
                    else:
                        ans += LENGTH_NOTIFICATION_EN
                    tk_count = total_token_count_from_response(resp)
                if resp.choices[0].finish_reason == "stop":
                    tk_count = total_token_count_from_response(resp)
                yield ans
        except Exception as e:
            yield ans + "\n**ERROR**: " + str(e)

        yield tk_count