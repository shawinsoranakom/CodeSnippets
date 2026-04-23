def excess_3_code(number: int) -> str:
  
    num = ""
    for digit in str(max(0, number)):
        num += str(bin(int(digit) + 3))[2:].zfill(4)
    return "0b" + num
