def check_vat_ru(self, vat):
        '''
        Check Russia VAT number.
        Method copied from vatnumber 1.2 lib https://code.google.com/archive/p/vatnumber/
        '''
        if len(vat) != 10 and len(vat) != 12:
            return False
        try:
            int(vat)
        except ValueError:
            return False

        if len(vat) == 10:
            check_sum = 2 * int(vat[0]) + 4 * int(vat[1]) + 10 * int(vat[2]) + \
                3 * int(vat[3]) + 5 * int(vat[4]) + 9 * int(vat[5]) + \
                4 * int(vat[6]) + 6 * int(vat[7]) + 8 * int(vat[8])
            check = check_sum % 11
            if check % 10 != int(vat[9]):
                return False
        else:
            check_sum1 = 7 * int(vat[0]) + 2 * int(vat[1]) + 4 * int(vat[2]) + \
                10 * int(vat[3]) + 3 * int(vat[4]) + 5 * int(vat[5]) + \
                9 * int(vat[6]) + 4 * int(vat[7]) + 6 * int(vat[8]) + \
                8 * int(vat[9])
            check = check_sum1 % 11

            if check != int(vat[10]):
                return False
            check_sum2 = 3 * int(vat[0]) + 7 * int(vat[1]) + 2 * int(vat[2]) + \
                4 * int(vat[3]) + 10 * int(vat[4]) + 3 * int(vat[5]) + \
                5 * int(vat[6]) + 9 * int(vat[7]) + 4 * int(vat[8]) + \
                6 * int(vat[9]) + 8 * int(vat[10])
            check = check_sum2 % 11
            if check != int(vat[11]):
                return False
        return True