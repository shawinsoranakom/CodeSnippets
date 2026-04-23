async def input(self, chunk):
        """
        Accumulates LMC chunks onto interpreter.messages.
        When it hits an "end" flag, calls interpreter.respond().
        """

        if "start" in chunk:
            # If the user is starting something, the interpreter should stop.
            if self.respond_thread is not None and self.respond_thread.is_alive():
                self.stop_event.set()
                self.respond_thread.join()
            self.accumulate(chunk)
        elif "content" in chunk:
            self.accumulate(chunk)
        elif "end" in chunk:
            # If the user is done talking, the interpreter should respond.

            run_code = None  # Will later default to auto_run unless the user makes a command here

            # But first, process any commands.
            if self.messages[-1].get("type") == "command":
                command = self.messages[-1]["content"]
                self.messages = self.messages[:-1]

                if command == "stop":
                    # Any start flag would have stopped it a moment ago, but to be sure:
                    self.stop_event.set()
                    self.respond_thread.join()
                    return
                if command == "go":
                    # This is to approve code.
                    run_code = True
                    pass

            self.stop_event.clear()
            self.respond_thread = threading.Thread(
                target=self.respond, args=(run_code,)
            )
            self.respond_thread.start()