def chat_streamly(self, system, history, gen_conf={}, **kwargs):
        if system and history and history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system})
        gen_conf = self._clean_conf(gen_conf)
        ans = ""
        total_tokens = 0
        try:
            response = self.client.chat_stream(model=self.model_name, messages=history, **gen_conf, **kwargs)
            for resp in response:
                if not resp.choices or not resp.choices[0].delta.content:
                    continue
                ans = resp.choices[0].delta.content
                total_tokens += 1
                if resp.choices[0].finish_reason == "length":
                    if is_chinese(ans):
                        ans += LENGTH_NOTIFICATION_CN
                    else:
                        ans += LENGTH_NOTIFICATION_EN
                yield ans

        except openai.APIError as e:
            yield ans + "\n**ERROR**: " + str(e)

        yield total_tokens