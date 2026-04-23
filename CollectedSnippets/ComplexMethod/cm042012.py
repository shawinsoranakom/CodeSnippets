def publish_message(self, msg):
        """If the role belongs to env, then the role's messages will be broadcast to env"""
        if not msg:
            return
        if MESSAGE_ROUTE_TO_SELF in msg.send_to:
            msg.send_to.add(any_to_str(self))
            msg.send_to.remove(MESSAGE_ROUTE_TO_SELF)
        if not msg.sent_from or msg.sent_from == MESSAGE_ROUTE_TO_SELF:
            msg.sent_from = any_to_str(self)
        if all(to in {any_to_str(self), self.name} for to in msg.send_to):  # Message to myself
            self.put_message(msg)
            return
        if not self.rc.env:
            # If env does not exist, do not publish the message
            return
        if isinstance(msg, AIMessage) and not msg.agent:
            msg.with_agent(self._setting)
        self.rc.env.publish_message(msg)