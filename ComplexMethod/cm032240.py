async def async_run(self):
        # 读取配置
        NEWBING_STYLE = get_conf("NEWBING_STYLE")
        from request_llms.bridge_all import model_info

        endpoint = model_info["newbing"]["endpoint"]
        while True:
            # 等待
            kwargs = self.child.recv()
            question = kwargs["query"]
            history = kwargs["history"]
            system_prompt = kwargs["system_prompt"]

            # 是否重置
            if len(self.local_history) > 0 and len(history) == 0:
                await self.newbing_model.reset()
                self.local_history = []

            # 开始问问题
            prompt = ""
            if system_prompt not in self.local_history:
                self.local_history.append(system_prompt)
                prompt += system_prompt + "\n"

            # 追加历史
            for ab in history:
                a, b = ab
                if a not in self.local_history:
                    self.local_history.append(a)
                    prompt += a + "\n"

            # 问题
            prompt += question
            self.local_history.append(question)
            print("question:", prompt)
            # 提交
            async for final, response in self.newbing_model.ask_stream(
                prompt=question,
                conversation_style=NEWBING_STYLE,  # ["creative", "balanced", "precise"]
                wss_link=endpoint,  # "wss://sydney.bing.com/sydney/ChatHub"
            ):
                if not final:
                    print(response)
                    self.child.send(str(response))
                else:
                    print("-------- receive final ---------")
                    self.child.send("[Finish]")