def complete(self, text, state):
        """Return the next possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.

        """
        if self.use_main_ns:
            self.namespace = __main__.__dict__

        if not text.strip():
            if state == 0:
                if _readline_available:
                    readline.insert_text('\t')
                    readline.redisplay()
                    return ''
                else:
                    return '\t'
            else:
                return None

        if state == 0:
            with warnings.catch_warnings(action="ignore"):
                if "." in text:
                    self.matches = self.attr_matches(text)
                else:
                    self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None