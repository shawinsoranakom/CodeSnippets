def expression(self, rbp=0):
        t = self.current_token
        self.current_token = self.next_token()
        left = t.nud(self)
        while rbp < self.current_token.lbp:
            t = self.current_token
            self.current_token = self.next_token()
            left = t.led(left, self)
        return left