def arithmetic_right_shift(number: int, shift_amount: int) -> str:
   
    if number >= 0: 
        binary_number = "0" + str(bin(number)).strip("-")[2:]
    else:  
        binary_number_length = len(bin(number)[3:])  
        binary_number = bin(abs(number) - (1 << binary_number_length))[3:]
        binary_number = (
            "1" + "0" * (binary_number_length - len(binary_number)) + binary_number
        )

    if shift_amount >= len(binary_number):
        return "0b" + binary_number[0] * len(binary_number)
    return (
        "0b"
        + binary_number[0] * shift_amount
        + binary_number[: len(binary_number) - shift_amount]
    )
