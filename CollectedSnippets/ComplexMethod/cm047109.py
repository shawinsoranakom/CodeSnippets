def _to_words(self, num=0):
        num_groups = self._split_number(num)
        sizeof_num_groups = len(num_groups)

        ret = [None] * (sizeof_num_groups + 1)
        ret_minus = ''

        if num < 0:
            ret_minus = self._minus + self._sep
        elif num == 0:
            return self._zero

        i = sizeof_num_groups - 1
        j = 1
        while i >= 0:
            if ret[j] is None:
                ret[j] = ''

            _pow = sizeof_num_groups - i

            if num_groups[i] != '000':
                if int(num_groups[i]) > 1:
                    if _pow == 1:
                        ret[j] += self._show_digits_group(num_groups[i], 0, not self._last_and and i) + self._sep
                        ret[j] += self._exponent[(_pow - 1) * 3]
                    elif _pow == 2:
                        ret[j] += self._show_digits_group(num_groups[i], -1, not self._last_and and i) + self._sep
                        ret[j] += self._misc_strings['hiliadi'] + self._sep
                    else:
                        ret[j] += self._show_digits_group(num_groups[i], 1, not self._last_and and i) + self._sep
                        ret[j] += self._exponent[(_pow - 1) * 3] + self._plural + self._sep
                else:
                    if _pow == 1:
                        ret[j] += self._show_digits_group(num_groups[i], 0, not self._last_and and i) + self._sep
                    elif _pow == 2:
                        ret[j] += self._exponent[(_pow - 1) * 3] + self._sep
                    else:
                        ret[j] += self._digits[1][1] + self._sep + self._exponent[(_pow - 1) * 3] + self._sep

            i -= 1
            j += 1

        ret = self._discard_empties(ret)
        ret.reverse()
        return ret_minus + ''.join(ret)