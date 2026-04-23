def parse(self):
        retval = self.expression()
        # Check that we have exhausted all the tokens
        if self.current_token is not EndToken:
            raise self.error_class(
                "Unused '%s' at end of if expression." % self.current_token.display()
            )
        return retval