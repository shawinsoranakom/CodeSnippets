async def _async_chat(self, history, gen_conf, **kwargs):
        logging.info("[HISTORY]" + json.dumps(history, ensure_ascii=False, indent=2))
        if self.model_name.lower().find("qwq") >= 0:
            logging.info(f"[INFO] {self.model_name} detected as reasoning model, using async_chat_streamly")

            final_ans = ""
            tol_token = 0
            async for delta, tol in self._async_chat_streamly(history, gen_conf, with_reasoning=False, **kwargs):
                if delta.startswith("<think>") or delta.endswith("</think>"):
                    continue
                final_ans += delta
                tol_token = tol

            if len(final_ans.strip()) == 0:
                final_ans = "**ERROR**: Empty response from reasoning model"

            return final_ans.strip(), tol_token

        _, kwargs = _apply_model_family_policies(
            self.model_name,
            backend="base",
            request_kwargs=kwargs,
        )

        response = await self.async_client.chat.completions.create(model=self.model_name, messages=history, **gen_conf, **kwargs)

        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            return "", 0
        ans = response.choices[0].message.content.strip()
        if response.choices[0].finish_reason == "length":
            ans = self._length_stop(ans)
        return ans, total_token_count_from_response(response)