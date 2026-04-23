def retrier_stmt(self):

        localctx = ASLParser.Retrier_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 176, self.RULE_retrier_stmt)
        try:
            self.state = 995
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [122]:
                self.enterOuterAlt(localctx, 1)
                self.state = 988
                self.error_equals_decl()
                pass
            elif token in [123]:
                self.enterOuterAlt(localctx, 2)
                self.state = 989
                self.interval_seconds_decl()
                pass
            elif token in [124]:
                self.enterOuterAlt(localctx, 3)
                self.state = 990
                self.max_attempts_decl()
                pass
            elif token in [125]:
                self.enterOuterAlt(localctx, 4)
                self.state = 991
                self.backoff_rate_decl()
                pass
            elif token in [126]:
                self.enterOuterAlt(localctx, 5)
                self.state = 992
                self.max_delay_seconds_decl()
                pass
            elif token in [127]:
                self.enterOuterAlt(localctx, 6)
                self.state = 993
                self.jitter_strategy_decl()
                pass
            elif token in [10]:
                self.enterOuterAlt(localctx, 7)
                self.state = 994
                self.comment_decl()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx