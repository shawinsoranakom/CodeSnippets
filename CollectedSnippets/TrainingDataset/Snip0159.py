def diophantine_all_soln(a: int, b: int, c: int, n: int = 2) -> None:
    
    (x0, y0) = diophantine(a, b, c)  
    d = greatest_common_divisor(a, b)
    p = a // d
    q = b // d

    for i in range(n):
        x = x0 + i * q
        y = y0 - i * p
        print(x, y)
