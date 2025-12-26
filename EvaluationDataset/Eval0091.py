def decimal_to_octal(num: int) -> str:
 
    octal = 0
    counter = 0
    while num > 0:
        remainder = num % 8
        octal = octal + (remainder * math.floor(math.pow(10, counter)))
        counter += 1
        num = math.floor(num / 8)  
    return f"0o{int(octal)}"
