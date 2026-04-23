def do(self) -> None:
        r = self.reader
        b = r.buffer
        for _ in range(r.get_arg()):
            x, y = r.pos2xy()
            new_y = y + 1

            if r.eol() == len(b):
                if r.historyi < len(r.history):
                    r.select_item(r.historyi + 1)
                    r.pos = r.eol(0)
                    return
                r.pos = len(b)
                r.error("end of buffer")
                return

            if (
                x
                > (
                    new_x := r.max_column(new_y)
                )  # we're past the end of the previous line
                or x == r.max_column(y)
                and any(
                    not i.isspace() for i in r.buffer[r.bol() :]
                )  # move between eols
            ):
                x = new_x

            r.setpos_from_xy(x, new_y)