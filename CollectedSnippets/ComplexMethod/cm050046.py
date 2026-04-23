def check_vat_tw(self, vat):
        """
        Since Feb. 2025, due to the imminent exhaustion of the UBN numbers, the validation logic was changed from using
        a division by 10 for the final check to using a division by 5, making numbers that were previously invalid now
        valid.

        The stdnum implementation of the VAT validation is not up to date with this latest update, so we implement our
        own validation to support these new valid UBNs.
        """
        vat = stdnum.util.get_cc_module("tw", "vat").compact(vat)
        if len(vat) != 8 or not vat.isdigit():
            return False  # The length is fixed, and we will expect it to be 8 in the following checks.

        logic_multiplier = [1, 2, 1, 2, 1, 2, 4, 1]  # This multiplier is set by the official validation logic.
        # Multiply each of the 8 digits of the VAT number by the corresponding digit of the logic multiplier.
        # For the next steps, we will need to sum the results.
        # For a two-digit product like 20, you would add its digits (2 + 0) to the total sum, so we convert the sums here
        # to strings in order to make it easier later on.
        products = [str(a * int(b)) for a, b in zip(logic_multiplier, vat)]
        if vat[6] != '7':
            # If the 7th number is not 7, we simply sum everything and check that the result is divisible by 5.
            checksum = sum(int(d) for d in ''.join(products))
            return checksum % 5 == 0
        else:
            # If the 7th number is 7, we calculate two sums:
            # z1: Calculate the total sum where the 7th position's contribution is taken as 1.
            # z2: Calculate the total sum where the 7th position's contribution is taken as 0.
            # The VAT number is valid if either Z1 or Z2 (or both) is evenly divisible by 5.
            base_checksum = sum(int(d) for d in "".join(products[0:6] + products[7:]))
            return (base_checksum + 1) % 5 == 0 or base_checksum % 5 == 0