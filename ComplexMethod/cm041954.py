async def _observe(self, ignore_memory=False) -> int:
        if self.status != RoleState.ALIVE:
            # 死者不再参与游戏
            return 0
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
        self.rc.news = [
            n for n in news if (n.cause_by in self.rc.watch or self.profile in n.send_to) and n not in old_messages
        ]

        # TODO to delete
        # await super()._observe()
        # # 只有发给全体的（""）或发给自己的（self.profile）消息需要走下面的_react流程，
        # # 其他的收听到即可，不用做动作
        # self.rc.news = [msg for msg in self.rc.news if msg.send_to in ["", self.profile]]
        return len(self.rc.news)