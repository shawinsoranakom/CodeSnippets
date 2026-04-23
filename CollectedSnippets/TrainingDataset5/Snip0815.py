def calculate_resistance(number_of_bands: int, color_code_list: list) -> dict:
    is_valid = check_validity(number_of_bands, color_code_list)
    if is_valid:
        number_of_significant_bands = get_band_type_count(
            number_of_bands, "significant"
        )
        significant_colors = color_code_list[:number_of_significant_bands]
        significant_digits = int(get_significant_digits(significant_colors))
        multiplier_color = color_code_list[number_of_significant_bands]
        multiplier = get_multiplier(multiplier_color)
        if number_of_bands == 3:
            tolerance_color = None
        else:
            tolerance_color = color_code_list[number_of_significant_bands + 1]
        tolerance = (
            20 if tolerance_color is None else get_tolerance(str(tolerance_color))
        )
        if number_of_bands != 6:
            temperature_coeffecient_color = None
        else:
            temperature_coeffecient_color = color_code_list[
                number_of_significant_bands + 2
            ]
        temperature_coeffecient = (
            0
            if temperature_coeffecient_color is None
            else get_temperature_coeffecient(str(temperature_coeffecient_color))
        )
        resisitance = significant_digits * multiplier
        if temperature_coeffecient == 0:
            answer = f"{resisitance}Ω ±{tolerance}% "
        else:
            answer = f"{resisitance}Ω ±{tolerance}% {temperature_coeffecient} ppm/K"
        return {"resistance": answer}
    else:
        raise ValueError("Input is invalid")
