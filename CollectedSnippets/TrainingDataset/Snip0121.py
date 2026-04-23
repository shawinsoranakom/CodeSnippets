def binary_coded_decimal(number: int) -> str:
  
    return "0b" + "".join(
        str(bin(int(digit)))[2:].zfill(4) for digit in str(max(0, number))
    )
