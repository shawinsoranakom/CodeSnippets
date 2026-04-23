async def _observe(self) -> int:
        if not self.rc.env:
            return 0
        news = []
        if not news:
            news = self.rc.msg_buffer.pop_all()
        old_messages = [] if not self.enable_memory else self.rc.memory.get()
        # Filter out messages of interest.
        self.rc.news = [
            n for n in news if (n.cause_by in self.rc.watch or self.name in n.send_to) and n not in old_messages
        ]

        if len(self.rc.news) == 1 and self.rc.news[0].cause_by == any_to_str(UserRequirement):
            logger.warning(f"Role: {self.name} add inner voice: {self.rc.news[0].content}")
            await self.add_inner_voice(self.rc.news[0].content)

        return 1