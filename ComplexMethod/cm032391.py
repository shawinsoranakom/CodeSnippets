async def stream_output_with_tools_async(self, prompt, msg, user_defined_prompt={}):
        if len(msg) > 3:
            st = timer()
            user_request = await full_question(messages=msg, chat_mdl=self.chat_mdl)
            self.callback("Multi-turn conversation optimization", {}, user_request, elapsed_time=timer() - st)
            msg = [*msg[:-1], {"role": "user", "content": user_request}]

        msg = self._fit_messages(prompt, msg)

        need2cite = self._param.cite and self._canvas.get_reference()["chunks"] and self._id.find("-->") < 0
        cited = False
        if need2cite and len(msg) < 7:
            self._append_system_prompt(msg, citation_prompt())
            cited = True

        answer = ""
        async for delta in self._generate_streamly(msg):
            if self.check_if_canceled("Agent streaming"):
                return
            if delta.find("**ERROR**") >= 0:
                if self.get_exception_default_value():
                    self.set_output("content", self.get_exception_default_value())
                    yield self.get_exception_default_value()
                else:
                    self.set_output("_ERROR", delta)
                return
            if not need2cite or cited:
                yield delta
            answer += delta

        if not need2cite or cited:
            artifact_md = self._collect_tool_artifact_markdown(existing_text=answer)
            if artifact_md:
                yield "\n\n" + artifact_md
                answer += "\n\n" + artifact_md
            self.set_output("content", answer)
            return

        st = timer()
        cited_answer = ""
        async for delta in self._gen_citations_async(answer):
            if self.check_if_canceled("Agent streaming"):
                return
            yield delta
            cited_answer += delta
        artifact_md = self._collect_tool_artifact_markdown(existing_text=cited_answer)
        if artifact_md:
            yield "\n\n" + artifact_md
            cited_answer += "\n\n" + artifact_md
        self.callback("gen_citations", {}, cited_answer, elapsed_time=timer() - st)
        self.set_output("content", cited_answer)