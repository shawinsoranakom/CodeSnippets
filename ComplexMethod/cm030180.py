def read_command(self, prompt):
        reply = self.read_input(prompt, multiline_block=False)
        if self.state == "dumb":
            # No logic applied whatsoever, just pass the raw reply back.
            return reply

        prefix = ""
        if self.state == "pdb":
            # PDB command entry mode
            cmd = self.pdb_instance.parseline(reply)[0]
            if cmd in self.pdb_commands or reply.strip() == "":
                # Recognized PDB command, or blank line repeating last command
                return reply

            # Otherwise, explicit or implicit exec command
            if reply.startswith("!"):
                prefix = "!"
                reply = reply.removeprefix(prefix).lstrip()

        if codeop.compile_command(reply + "\n", "<stdin>", "single") is not None:
            # Valid single-line statement
            return prefix + reply

        # Otherwise, valid first line of a multi-line statement
        more_prompt = "...".ljust(len(prompt))
        while codeop.compile_command(reply, "<stdin>", "single") is None:
            reply += "\n" + self.read_input(more_prompt, multiline_block=True)

        return prefix + reply