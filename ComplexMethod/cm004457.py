def convert(self, number):
        """
        Converts an individual number passed in string form to spelt-out form
        """
        if "." in number:
            integer_part, decimal_part = number.split(".")
        else:
            integer_part, decimal_part = number, "00"

        # Extract currency symbol if present
        currency_symbol = ""
        for symbol, name in self.currency_symbols.items():
            if integer_part.startswith(symbol):
                currency_symbol = name
                integer_part = integer_part[len(symbol) :]
                break

            if integer_part.startswith("-"):
                if integer_part[1:].startswith(symbol):
                    currency_symbol = name
                    integer_part = "-" + integer_part[len(symbol) + 1 :]
                    break

        # Extract 'minus' prefix for negative numbers
        minus_prefix = ""
        if integer_part.startswith("-"):
            minus_prefix = "minus "
            integer_part = integer_part[1:]
        elif integer_part.startswith("minus"):
            minus_prefix = "minus "
            integer_part = integer_part[len("minus") :]

        percent_suffix = ""
        if "%" in integer_part or "%" in decimal_part:
            percent_suffix = " percent"
            integer_part = integer_part.replace("%", "")
            decimal_part = decimal_part.replace("%", "")

        integer_part = integer_part.zfill(3 * ((len(integer_part) - 1) // 3 + 1))

        parts = []
        for i in range(0, len(integer_part), 3):
            chunk = int(integer_part[i : i + 3])
            if chunk > 0:
                part = self.spell_number(chunk)
                unit = self.thousands[len(integer_part[i:]) // 3 - 1]
                if unit:
                    part += " " + unit
                parts.append(part)

        spelled_integer = " ".join(parts)

        # Format the spelt-out number based on conditions, such as:
        # If it has decimal parts, currency symbol, minus prefix, etc
        if decimal_part == "00":
            return (
                f"{minus_prefix}{spelled_integer}{percent_suffix}{currency_symbol}"
                if minus_prefix or currency_symbol
                else f"{spelled_integer}{percent_suffix}"
            )
        else:
            spelled_decimal = " ".join([self.spell_number(int(digit)) for digit in decimal_part])
            return (
                f"{minus_prefix}{spelled_integer} point {spelled_decimal}{percent_suffix}{currency_symbol}"
                if minus_prefix or currency_symbol
                else f"{minus_prefix}{spelled_integer} point {spelled_decimal}{percent_suffix}"
            )