def begin(self, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
        # main plugin function
        self.init(chatbot)
        chatbot.append(["[ 请讲话 ]", "[ 正在等您说完问题 ]"])
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        self.plugin_wd.begin_watch()
        self.agt = AsyncGptTask()
        self.commit_wd = WatchDog(timeout=self.commit_after_pause_n_second, bark_fn=self.no_audio_for_a_while, interval=0.2)
        self.commit_wd.begin_watch()

        while not self.stop:
            self.event_on_result_chg.wait(timeout=0.25)  # run once every 0.25 second
            chatbot = self.agt.update_chatbot(chatbot)   # 将子线程的gpt结果写入chatbot
            history = chatbot2history(chatbot)
            yield from update_ui(chatbot=chatbot, history=history)      # 刷新界面
            self.plugin_wd.feed()

            if self.event_on_result_chg.is_set():
                # called when some words have finished
                self.event_on_result_chg.clear()
                chatbot[-1] = list(chatbot[-1])
                chatbot[-1][0] = self.buffered_sentence + self.parsed_text
                history = chatbot2history(chatbot)
                yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
                self.commit_wd.feed()

            if self.event_on_entence_end.is_set():
                # called when a sentence has ended
                self.event_on_entence_end.clear()
                self.parsed_text = self.parsed_sentence
                self.buffered_sentence += self.parsed_text
                chatbot[-1] = list(chatbot[-1])
                chatbot[-1][0] = self.buffered_sentence
                history = chatbot2history(chatbot)
                yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面

            if self.event_on_commit_question.is_set():
                # called when a question should be commited
                self.event_on_commit_question.clear()
                if len(self.buffered_sentence) == 0: raise RuntimeError

                self.commit_wd.begin_watch()
                chatbot[-1] = list(chatbot[-1])
                chatbot[-1] = [self.buffered_sentence, "[ 等待GPT响应 ]"]
                yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
                # add gpt task 创建子线程请求gpt，避免线程阻塞
                history = chatbot2history(chatbot)
                self.agt.add_async_gpt_task(self.buffered_sentence, len(chatbot)-1, llm_kwargs, history, system_prompt)

                self.buffered_sentence = ""
                chatbot.append(["[ 请讲话 ]", "[ 正在等您说完问题 ]"])
                yield from update_ui(chatbot=chatbot, history=history) # 刷新界面

            if not self.event_on_result_chg.is_set() and not self.event_on_entence_end.is_set() and not self.event_on_commit_question.is_set():
                visualize_audio(chatbot, self.audio_shape)
                yield from update_ui(chatbot=chatbot, history=history) # 刷新界面

        if len(self.stop_msg) != 0:
            raise RuntimeError(self.stop_msg)