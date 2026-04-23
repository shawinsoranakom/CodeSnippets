async def _observe(self) -> int:
        """Prepare new messages for processing from the message buffer and other sources."""
        # Read unprocessed messages from the msg buffer.
        news = []
        if self.recovered and self.latest_observed_msg:
            news = self.rc.memory.find_news(observed=[self.latest_observed_msg], k=10)
        if not news:
            news = self.rc.msg_buffer.pop_all()
        # Store the read messages in your own memory to prevent duplicate processing.
        old_messages = [] if not self.enable_memory else self.rc.memory.get()
        # Filter in messages of interest.
        self.rc.news = [
            n for n in news if (n.cause_by in self.rc.watch or self.name in n.send_to) and n not in old_messages
        ]
        if self.observe_all_msg_from_buffer:
            # save all new messages from the buffer into memory, the role may not react to them but can be aware of them
            self.rc.memory.add_batch(news)
        else:
            # only save messages of interest into memory
            self.rc.memory.add_batch(self.rc.news)
        self.latest_observed_msg = self.rc.news[-1] if self.rc.news else None  # record the latest observed msg

        # Design Rules:
        # If you need to further categorize Message objects, you can do so using the Message.set_meta function.
        # msg_buffer is a receiving buffer, avoid adding message data and operations to msg_buffer.
        news_text = [f"{i.role}: {i.content[:20]}..." for i in self.rc.news]
        if news_text:
            logger.debug(f"{self._setting} observed: {news_text}")
        return len(self.rc.news)