def process_arabic_group(self, group_number, group_level,
                             remaining_number):
        tens = Decimal(group_number) % Decimal(100)
        hundreds = Decimal(group_number) / Decimal(100)
        ret_val = ""

        if int(hundreds) > 0:
            if tens == 0 and int(hundreds) == 2:
                ret_val = f"{self.arabicAppendedTwos[0]}"
            else:
                ret_val = f"{self.arabicHundreds[int(hundreds)]}"
                if ret_val and tens != 0:
                    ret_val += " و "

        if tens > 0:
            if tens < 20:
                # if int(group_level) >= len(self.arabicTwos):
                #     raise OverflowError(self.errmsg_toobig %
                #                         (self.number, self.MAXVAL))
                assert int(group_level) < len(self.arabicTwos)
                if tens == 2 and int(hundreds) == 0 and group_level > 0:
                    power = int(math.log10(self.integer_value))
                    if self.integer_value > 10 and power % 3 == 0 and \
                            self.integer_value == 2 * (10 ** power):
                        ret_val = f"{self.arabicAppendedTwos[int(group_level)]}"
                    else:
                        ret_val = f"{self.arabicTwos[int(group_level)]}"
                else:
                    if tens == 1 and group_level > 0 and hundreds == 0:
                        # Note: this never happens
                        # (hundreds == 0 only if group_number is 0)
                        ret_val += ""
                    elif (tens == 1 or tens == 2) and (
                            group_level == 0 or group_level == -1) and \
                            hundreds == 0 and remaining_number == 0:
                        # Note: this never happens (idem)
                        ret_val += ""
                    elif tens == 1 and group_level > 0:
                        ret_val += self.arabicGroup[int(group_level)]
                    else:
                        ret_val += self.digit_feminine_status(int(tens),
                                                              group_level)
            else:
                ones = tens % 10
                tens = (tens / 10) - 2
                if ones > 0:
                    ret_val += self.digit_feminine_status(ones, group_level)
                if ret_val and ones != 0:
                    ret_val += " و "

                ret_val += self.arabicTens[int(tens)]

        return ret_val