def _get_pass(self, prompt="Password: "):
        p = getpass.getpass(prompt=prompt)
        if not p:
            raise CommandError("aborted")
        return p