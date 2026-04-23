def exponential_moving_average(
    stock_prices: Iterator[float], window_size: int
) -> Iterator[float]:

    if window_size <= 0:
        raise ValueError("window_size must be > 0")

    alpha = 2 / (1 + window_size)

    moving_average = 0.0

    for i, stock_price in enumerate(stock_prices):
        if i <= window_size:
            moving_average = (moving_average + stock_price) * 0.5 if i else stock_price
        else:
            moving_average = (alpha * stock_price) + ((1 - alpha) * moving_average)
        yield moving_average
