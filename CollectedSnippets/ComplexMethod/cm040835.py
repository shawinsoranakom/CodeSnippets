def assign_template_value_terminal(self):

        localctx = ASLParser.Assign_template_value_terminalContext(self, self._ctx, self.state)
        self.enterRule(localctx, 88, self.RULE_assign_template_value_terminal)
        self._la = 0 # Token type
        try:
            self.state = 612
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,36,self._ctx)
            if la_ == 1:
                localctx = ASLParser.Assign_template_value_terminal_floatContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 606
                self.match(ASLParser.NUMBER)
                pass

            elif la_ == 2:
                localctx = ASLParser.Assign_template_value_terminal_intContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 607
                self.match(ASLParser.INT)
                pass

            elif la_ == 3:
                localctx = ASLParser.Assign_template_value_terminal_boolContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 608
                _la = self._input.LA(1)
                if not(_la==7 or _la==8):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass

            elif la_ == 4:
                localctx = ASLParser.Assign_template_value_terminal_nullContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 609
                self.match(ASLParser.NULL)
                pass

            elif la_ == 5:
                localctx = ASLParser.Assign_template_value_terminal_string_jsonataContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 610
                self.string_jsonata()
                pass

            elif la_ == 6:
                localctx = ASLParser.Assign_template_value_terminal_string_literalContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 611
                self.string_literal()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx