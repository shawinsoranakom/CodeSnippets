def unclosed_block_tag(self, parse_until):
        command, token = self.command_stack.pop()
        msg = "Unclosed tag on line %d: '%s'. Looking for one of: %s." % (
            token.lineno,
            command,
            ", ".join(parse_until),
        )
        raise self.error(token, msg)