async def _quick_think(self) -> Tuple[Message, str]:
        answer = ""
        rsp_msg = None
        if self.rc.news[-1].cause_by != any_to_str(UserRequirement):
            # Agents themselves won't generate quick questions, use this rule to reduce extra llm calls
            return rsp_msg, ""

        # routing
        memory = self.get_memories(k=self.memory_k)
        context = self.llm.format_msg(memory + [UserMessage(content=QUICK_THINK_PROMPT)])
        async with ThoughtReporter() as reporter:
            await reporter.async_report({"type": "classify"})
            intent_result = await self.llm.aask(context, system_msgs=[self.format_quick_system_prompt()])

        if "QUICK" in intent_result or "AMBIGUOUS" in intent_result:  # llm call with the original context
            async with ThoughtReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report({"type": "quick"})
                answer = await self.llm.aask(
                    self.llm.format_msg(memory),
                    system_msgs=[QUICK_RESPONSE_SYSTEM_PROMPT.format(role_info=self._get_prefix())],
                )
            # If the answer contains the substring '[Message] from A to B:', remove it.
            pattern = r"\[Message\] from .+? to .+?:\s*"
            answer = re.sub(pattern, "", answer, count=1)
            if "command_name" in answer:
                # an actual TASK intent misclassified as QUICK, correct it here, FIXME: a better way is to classify it correctly in the first place
                answer = ""
                intent_result = "TASK"
        elif "SEARCH" in intent_result:
            query = "\n".join(str(msg) for msg in memory)
            answer = await SearchEnhancedQA().run(query)

        if answer:
            self.rc.memory.add(AIMessage(content=answer, cause_by=QUICK_THINK_TAG))
            await self.reply_to_human(content=answer)
            rsp_msg = AIMessage(
                content=answer,
                sent_from=self.name,
                cause_by=QUICK_THINK_TAG,
            )

        return rsp_msg, intent_result