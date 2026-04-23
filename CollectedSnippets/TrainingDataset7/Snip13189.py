def skip_past(self, endtag):
        while self.tokens:
            token = self.next_token()
            if token.token_type == TokenType.BLOCK and token.contents == endtag:
                return
        self.unclosed_block_tag([endtag])