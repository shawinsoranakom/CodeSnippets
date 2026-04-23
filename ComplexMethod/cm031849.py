def buildmap(self):
        for c1 in range(0, 256):
            if c1 not in self.encode_map:
                continue
            c2map = self.encode_map[c1]
            rc2values = [k for k in c2map.keys()]
            rc2values.sort()
            if not rc2values:
                continue

            c2map[self.prefix] = True
            c2map['min'] = rc2values[0]
            c2map['max'] = rc2values[-1]
            c2map['midx'] = len(self.filler)

            for v in range(rc2values[0], rc2values[-1] + 1):
                if v not in c2map:
                    self.write_nochar()
                elif isinstance(c2map[v], int):
                    self.write_char(c2map[v])
                elif isinstance(c2map[v], tuple):
                    self.write_multic(c2map[v])
                else:
                    raise ValueError