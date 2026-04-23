def get_num_string(self, number: float | complex) -> str:
        if isinstance(number, complex):
            if self.hide_zero_components_on_complex and number.imag == 0:
                number = number.real
                formatter = self.get_formatter()
            elif self.hide_zero_components_on_complex and number.real == 0:
                number = number.imag
                formatter = self.get_formatter() + "i"
            else:
                formatter = self.get_complex_formatter()
        else:
            formatter = self.get_formatter()
        if self.num_decimal_places == 0 and isinstance(number, float):
            number = int(number)
        num_string = formatter.format(number)

        rounded_num = np.round(number, self.num_decimal_places)
        if num_string.startswith("-") and rounded_num == 0:
            if self.include_sign:
                num_string = "+" + num_string[1:]
            else:
                num_string = num_string[1:]
        num_string = num_string.replace("-", "–")
        return num_string