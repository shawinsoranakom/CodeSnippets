def string_literal(self):

        localctx = ASLParser.String_literalContext(self, self._ctx, self.state)
        self.enterRule(localctx, 228, self.RULE_string_literal)
        try:
            self.state = 1149
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [159]:
                self.enterOuterAlt(localctx, 1)
                self.state = 1142
                self.match(ASLParser.STRING)
                pass
            elif token in [153]:
                self.enterOuterAlt(localctx, 2)
                self.state = 1143
                self.match(ASLParser.STRINGDOLLAR)
                pass
            elif token in [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 119, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 134, 135, 136]:
                self.enterOuterAlt(localctx, 3)
                self.state = 1144
                self.soft_string_keyword()
                pass
            elif token in [30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70]:
                self.enterOuterAlt(localctx, 4)
                self.state = 1145
                self.comparison_op()
                pass
            elif token in [29, 38, 49]:
                self.enterOuterAlt(localctx, 5)
                self.state = 1146
                self.choice_operator()
                pass
            elif token in [137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152]:
                self.enterOuterAlt(localctx, 6)
                self.state = 1147
                self.states_error_name()
                pass
            elif token in [154, 155, 156, 157, 158]:
                self.enterOuterAlt(localctx, 7)
                self.state = 1148
                self.string_expression()
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