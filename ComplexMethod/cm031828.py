def maybe_indent(self, txt: str) -> None:
        parens = txt.count("(") - txt.count(")")
        if parens > 0:
            if self.last_token:
                offset = self.last_token.end_column - 1
                if offset <= self.indents[-1] or offset > 40:
                    offset = self.indents[-1] + 4
            else:
                offset = self.indents[-1] + 4
            self.indents.append(offset)
        if is_label(txt):
            self.indents.append(self.indents[-1] + 4)
        else:
            braces = txt.count("{") - txt.count("}")
            if braces > 0:
                assert braces == 1
                if 'extern "C"' in txt:
                    self.indents.append(self.indents[-1])
                else:
                    self.indents.append(self.indents[-1] + 4)