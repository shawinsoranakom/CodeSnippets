def payload_value_lit(self):

        localctx = ASLParser.Payload_value_litContext(self, self._ctx, self.state)
        self.enterRule(localctx, 72, self.RULE_payload_value_lit)
        self._la = 0 # Token type
        try:
            self.state = 539
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [161]:
                localctx = ASLParser.Payload_value_floatContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 534
                self.match(ASLParser.NUMBER)
                pass
            elif token in [160]:
                localctx = ASLParser.Payload_value_intContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 535
                self.match(ASLParser.INT)
                pass
            elif token in [7, 8]:
                localctx = ASLParser.Payload_value_boolContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 536
                _la = self._input.LA(1)
                if not(_la==7 or _la==8):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass
            elif token in [9]:
                localctx = ASLParser.Payload_value_nullContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 537
                self.match(ASLParser.NULL)
                pass
            elif token in [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 119, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159]:
                localctx = ASLParser.Payload_value_strContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 538
                self.string_literal()
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