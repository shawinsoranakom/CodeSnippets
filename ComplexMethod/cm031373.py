def push(self, evt):
        if self.verbose:
            print("pushed", evt.data, end="")
        key = evt.data
        d = self.k.get(key)
        if isinstance(d, dict):
            if self.verbose:
                print("transition")
            self.stack.append(key)
            self.k = d
        else:
            if d is None:
                if self.verbose:
                    print("invalid")
                if self.stack or len(key) > 1 or unicodedata.category(key) == "C":
                    self.results.append((self.invalid_cls, self.stack + [key]))
                else:
                    # small optimization:
                    self.k[key] = self.character_cls
                    self.results.append((self.character_cls, [key]))
            else:
                if self.verbose:
                    print("matched", d)
                self.results.append((d, self.stack + [key]))
            self.stack = []
            self.k = self.ck