def inst_header(self) -> InstHeader | None:
        # annotation* inst(NAME, (inputs -- outputs))
        # | annotation* op(NAME, (inputs -- outputs))
        annotations = []
        while anno := self.expect(lx.ANNOTATION):
            if anno.text == "replicate":
                self.require(lx.LPAREN)
                stop = self.require(lx.NUMBER)
                start_text = "0"
                if self.expect(lx.COLON):
                    start_text = stop.text
                    stop = self.require(lx.NUMBER)
                self.require(lx.RPAREN)
                annotations.append(f"replicate({start_text}:{stop.text})")
            else:
                annotations.append(anno.text)
        tkn = self.expect(lx.INST)
        if not tkn:
            tkn = self.expect(lx.OP)
        if tkn:
            kind = cast(Literal["inst", "op"], tkn.text)
            if self.expect(lx.LPAREN) and (tkn := self.expect(lx.IDENTIFIER)):
                name = tkn.text
                if self.expect(lx.COMMA):
                    inp, outp = self.io_effect()
                    if self.expect(lx.RPAREN):
                        if (tkn := self.peek()) and tkn.kind == lx.LBRACE:
                            return InstHeader(annotations, kind, name, inp, outp)
        return None