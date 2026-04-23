def switch(self, an_input: str) -> list[str]:
        """Process and dispatch input.

        Returns
        ----------
        List[str]
            list of commands in the queue to execute
        """
        actions = self.parse_input(an_input)

        if an_input and an_input != "reset":
            session.console.print()

        # Empty command
        if len(actions) == 0:
            pass

        # Navigation slash is being used first split commands
        elif len(actions) > 1:
            # Absolute path is specified
            if not actions[0]:
                actions[0] = "home"

            # Add all instructions to the queue
            for cmd in actions[::-1]:
                if cmd:
                    self.queue.insert(0, cmd)

        # Single command fed, process
        else:
            try:
                known_args, other_args = self.parser.parse_known_args(
                    shlex.split(an_input)
                )
            except Exception as exc:
                raise SystemExit from exc

            if RECORD_SESSION:
                SESSION_RECORDED.append(an_input)

            # Redirect commands to their correct functions
            if known_args.cmd:
                if known_args.cmd in ("..", "q"):
                    known_args.cmd = "quit"
                elif known_args.cmd in ("e"):
                    known_args.cmd = "exit"
                elif known_args.cmd in ("?", "h"):
                    known_args.cmd = "help"
                elif known_args.cmd == "r":
                    known_args.cmd = "reset"

            getattr(
                self,
                "call_" + known_args.cmd,
                lambda _: "Command not recognized!",
            )(other_args)

        if (
            an_input
            and an_input != "reset"
            and (
                not self.queue or (self.queue and self.queue[0] not in ("quit", "help"))
            )
        ):
            session.console.print()

        return self.queue