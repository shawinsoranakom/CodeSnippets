def step(self, prompt, chatbot, history):

        """
        首先，处理游戏初始化等特殊情况
        """
        if self.step_cnt == 0:
            self.begin_game_step_0(prompt, chatbot, history)
            self.lock_plugin(chatbot)
            self.cur_task = 'head_start'
        else:
            if prompt.strip() == 'exit' or prompt.strip() == '结束剧情':
                # should we terminate game here?
                self.delete_game = True
                yield from update_ui_latest_msg(lastmsg=f"游戏结束。", chatbot=chatbot, history=history, delay=0.)
                return
            if '剧情收尾' in prompt:
                self.cur_task = 'story_terminate'
            # # well, game resumes
            # chatbot.append([prompt, ""])
        # update ui, don't keep the user waiting
        yield from update_ui(chatbot=chatbot, history=history)


        """
        处理游戏的主体逻辑
        """
        if self.cur_task == 'head_start':
            """
            这是游戏的第一步
            """
            inputs_ = prompts_hs.format(headstart=self.headstart)
            history_ = []
            story_paragraph = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs_, '故事开头', self.llm_kwargs,
                chatbot, history_, self.sys_prompt_
            )
            self.story.append(story_paragraph)
            # # 配图
            yield from update_ui_latest_msg(lastmsg=story_paragraph + '<br/>正在生成插图中 ...', chatbot=chatbot, history=history, delay=0.)
            yield from update_ui_latest_msg(lastmsg=story_paragraph + '<br/>'+ self.generate_story_image(story_paragraph), chatbot=chatbot, history=history, delay=0.)

            # # 构建后续剧情引导
            previously_on_story = ""
            for s in self.story:
                previously_on_story += s + '\n'
            inputs_ = prompts_interact.format(previously_on_story=previously_on_story)
            history_ = []
            self.next_choices = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs_, '请在以下几种故事走向中，选择一种（当然，您也可以选择给出其他故事走向）：', self.llm_kwargs,
                chatbot,
                history_,
                self.sys_prompt_
            )
            self.cur_task = 'user_choice'


        elif self.cur_task == 'user_choice':
            """
            根据用户的提示，确定故事的下一步
            """
            if '请在以下几种故事走向中，选择一种' in chatbot[-1][0]: chatbot.pop(-1)
            previously_on_story = ""
            for s in self.story:
                previously_on_story += s + '\n'
            inputs_ = prompts_resume.format(previously_on_story=previously_on_story, choice=self.next_choices, user_choice=prompt)
            history_ = []
            story_paragraph = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs_, f'下一段故事（您的选择是：{prompt}）。', self.llm_kwargs,
                chatbot, history_, self.sys_prompt_
            )
            self.story.append(story_paragraph)
            # # 配图
            yield from update_ui_latest_msg(lastmsg=story_paragraph + '<br/>正在生成插图中 ...', chatbot=chatbot, history=history, delay=0.)
            yield from update_ui_latest_msg(lastmsg=story_paragraph + '<br/>'+ self.generate_story_image(story_paragraph), chatbot=chatbot, history=history, delay=0.)

            # # 构建后续剧情引导
            previously_on_story = ""
            for s in self.story:
                previously_on_story += s + '\n'
            inputs_ = prompts_interact.format(previously_on_story=previously_on_story)
            history_ = []
            self.next_choices = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs_,
                '请在以下几种故事走向中，选择一种。当然，您也可以给出您心中的其他故事走向。另外，如果您希望剧情立即收尾，请输入剧情走向，并以“剧情收尾”四个字提示程序。', self.llm_kwargs,
                chatbot,
                history_,
                self.sys_prompt_
            )
            self.cur_task = 'user_choice'


        elif self.cur_task == 'story_terminate':
            """
            根据用户的提示，确定故事的结局
            """
            previously_on_story = ""
            for s in self.story:
                previously_on_story += s + '\n'
            inputs_ = prompts_terminate.format(previously_on_story=previously_on_story, user_choice=prompt)
            history_ = []
            story_paragraph = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs_, f'故事收尾（您的选择是：{prompt}）。', self.llm_kwargs,
                chatbot, history_, self.sys_prompt_
            )
            # # 配图
            yield from update_ui_latest_msg(lastmsg=story_paragraph + '<br/>正在生成插图中 ...', chatbot=chatbot, history=history, delay=0.)
            yield from update_ui_latest_msg(lastmsg=story_paragraph + '<br/>'+ self.generate_story_image(story_paragraph), chatbot=chatbot, history=history, delay=0.)

            # terminate game
            self.delete_game = True
            return