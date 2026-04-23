def _show_digits_group(self, num, gender=0, last=False):
        num = int(num)
        e = int(num % 10)                # ones
        d = int((num - e) % 100 / 10)        # tens
        s = int((num - d * 10 - e) % 1000 / 100)  # hundreds
        ret = [None] * 6

        if s:
            if s == 1:
                ret[1] = self._misc_strings['sto']
            elif s == 2 or s == 3:
                ret[1] = self._digits[0][s] + self._misc_strings['sta']
            else:
                ret[1] = self._digits[0][s] + self._misc_strings['stotin']

        if d:
            if d == 1:
                if not e:
                    ret[3] = self._misc_strings['deset']
                else:
                    if e == 1:
                        ret[3] = self._misc_strings['edinadeset']
                    else:
                        ret[3] = self._digits[1][e] + self._misc_strings['na'] + self._misc_strings['deset']
                    e = 0
            else:
                ret[3] = self._digits[1][d] + self._misc_strings['deset']

        if e:
            ret[5] = self._digits[gender][e]

        if len(self._discard_empties(ret)) > 1:
            if e:
                ret[4] = self._and
            else:
                ret[2] = self._and

        if last:
            if not s or len(self._discard_empties(ret)) == 1:
                ret[0] = self._and
            self._last_and = True

        return self._sep.join(self._discard_empties(ret))