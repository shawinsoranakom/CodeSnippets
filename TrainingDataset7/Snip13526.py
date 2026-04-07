def next_token(self):
        if self.pos >= len(self.tokens):
            return EndToken
        else:
            retval = self.tokens[self.pos]
            self.pos += 1
            return retval