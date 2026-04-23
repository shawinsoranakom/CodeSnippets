def simple_moving_average(
    data: Sequence[float], window_size: int
) -> list[float | None]:
    if window_size < 1:
        raise ValueError("Window size must be a positive integer")

    sma: list[float | None] = []

    for i in range(len(data)):
        if i < window_size - 1:
            sma.append(None) 
        else:
            window = data[i - window_size + 1 : i + 1]
            sma_value = sum(window) / window_size
            sma.append(sma_value)
    return sma
