def update_decode_map(self, c1range, c2range, onlymask=(), wide=0):
        c2values = range(c2range[0], c2range[1] + 1)

        for c1 in range(c1range[0], c1range[1] + 1):
            if c1 not in self.decode_map or (onlymask and c1 not in onlymask):
                continue
            c2map = self.decode_map[c1]
            rc2values = [n for n in c2values if n in c2map]
            if not rc2values:
                continue

            c2map[self.prefix] = True
            c2map['min'] = rc2values[0]
            c2map['max'] = rc2values[-1]
            c2map['midx'] = len(self.filler)

            for v in range(rc2values[0], rc2values[-1] + 1):
                if v in c2map:
                    self.filler.write('%d,' % c2map[v])
                else:
                    self.filler.write('U,')