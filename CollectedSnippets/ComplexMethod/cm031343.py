def do(self) -> None:
        r = self.reader
        b = r.buffer
        if self.event[-1] == "\004":
            if b and b[-1].endswith("\n"):
                self.finish = True
            elif (
                r.pos == 0
                and len(b) == 0  # this is something of a hack
            ):
                r.update_screen()
                r.console.finish()
                raise EOFError

        changed_from: int | None = None
        for i in range(r.get_arg()):
            if r.pos != len(b):
                del b[r.pos]
                changed_from = r.pos if changed_from is None else min(changed_from, r.pos)
            else:
                self.reader.error("end of buffer")
        if changed_from is not None:
            r.invalidate_buffer(changed_from)