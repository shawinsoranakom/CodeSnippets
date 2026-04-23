async def _observe(self, ignore_memory=False) -> int:
        news = []
        if not news:
            news = self.rc.msg_buffer.pop_all()
        old_messages = [] if ignore_memory else self.rc.memory.get()
        for m in news:
            if len(m.restricted_to) and self.profile not in m.restricted_to and self.name not in m.restricted_to:
                # if the msg is not send to the whole audience ("") nor this role (self.profile or self.name),
                # then this role should not be able to receive it and record it into its memory
                continue
            self.rc.memory.add(m)
        # add `MESSAGE_ROUTE_TO_ALL in n.send_to` make it to run `ParseSpeak`
        self.rc.news = [
            n
            for n in news
            if (n.cause_by in self.rc.watch or self.profile in n.send_to or MESSAGE_ROUTE_TO_ALL in n.send_to)
            and n not in old_messages
        ]
        return len(self.rc.news)