def isearch_next(self) -> None:
        st = self.isearch_term
        p = self.pos
        i = self.historyi
        s = self.get_unicode()
        forwards = self.isearch_direction == ISEARCH_DIRECTION_FORWARDS
        while 1:
            if forwards:
                p = s.find(st, p + 1)
            else:
                p = s.rfind(st, 0, p + len(st) - 1)
            if p != -1:
                self.select_item(i)
                self.pos = p
                return
            elif (forwards and i >= len(self.history) - 1) or (not forwards and i == 0):
                self.error("not found")
                return
            else:
                if forwards:
                    i += 1
                    s = self.get_item(i)
                    p = -1
                else:
                    i -= 1
                    s = self.get_item(i)
                    p = len(s)