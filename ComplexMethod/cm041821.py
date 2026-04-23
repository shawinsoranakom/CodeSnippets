def chat(self, message=None, display=True, stream=False, blocking=True):
        try:
            self.responding = True
            if self.anonymous_telemetry:
                message_type = type(
                    message
                ).__name__  # Only send message type, no content
                send_telemetry(
                    "started_chat",
                    properties={
                        "in_terminal_interface": self.in_terminal_interface,
                        "message_type": message_type,
                        "os_mode": self.os,
                    },
                )

            if not blocking:
                chat_thread = threading.Thread(
                    target=self.chat, args=(message, display, stream, True)
                )  # True as in blocking = True
                chat_thread.start()
                return

            if stream:
                return self._streaming_chat(message=message, display=display)

            # If stream=False, *pull* from the stream.
            for _ in self._streaming_chat(message=message, display=display):
                pass

            # Return new messages
            self.responding = False
            return self.messages[self.last_messages_count :]

        except GeneratorExit:
            self.responding = False
            # It's fine
        except Exception as e:
            self.responding = False
            if self.anonymous_telemetry:
                message_type = type(message).__name__
                send_telemetry(
                    "errored",
                    properties={
                        "error": str(e),
                        "in_terminal_interface": self.in_terminal_interface,
                        "message_type": message_type,
                        "os_mode": self.os,
                    },
                )

            raise