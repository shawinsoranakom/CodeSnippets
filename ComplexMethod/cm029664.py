def __calc_alt_digits(self):
        # Set self.LC_alt_digits by using time.strftime().

        # The magic data should contain all decimal digits.
        time_tuple = time.struct_time((1998, 1, 27, 10, 43, 56, 1, 27, 0))
        s = time.strftime("%x%X", time_tuple)
        if s.isascii():
            # Fast path -- all digits are ASCII.
            self.LC_alt_digits = ()
            return

        digits = ''.join(sorted(set(re.findall(r'\d', s))))
        if len(digits) == 10 and ord(digits[-1]) == ord(digits[0]) + 9:
            # All 10 decimal digits from the same set.
            if digits.isascii():
                # All digits are ASCII.
                self.LC_alt_digits = ()
                return

            self.LC_alt_digits = [a + b for a in digits for b in digits]
            # Test whether the numbers contain leading zero.
            time_tuple2 = time.struct_time((2000, 1, 1, 1, 1, 1, 5, 1, 0))
            if self.LC_alt_digits[1] not in time.strftime("%x %X", time_tuple2):
                self.LC_alt_digits[:10] = digits
            return

        # Either non-Gregorian calendar or non-decimal numbers.
        if {'\u4e00', '\u4e03', '\u4e5d', '\u5341', '\u5eff'}.issubset(s):
            # lzh_TW
            self.LC_alt_digits = lzh_TW_alt_digits
            return

        self.LC_alt_digits = None