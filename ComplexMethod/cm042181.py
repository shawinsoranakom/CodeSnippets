def fft_next_good_size(n: int) -> int:
    """
    smallest composite of 2, 3, 5, 7, 11 that is >= n
    inspired by pocketfft
    """
    if n <= 6:
      return n
    best, f2 = 2 * n, 1
    while f2 < best:
        f23 = f2
        while f23 < best:
            f235 = f23
            while f235 < best:
                f2357 = f235
                while f2357 < best:
                    f235711 = f2357
                    while f235711 < best:
                        best = f235711 if f235711 >= n else best
                        f235711 *= 11
                    f2357 *= 7
                f235 *= 5
            f23 *= 3
        f2 *= 2
    return best