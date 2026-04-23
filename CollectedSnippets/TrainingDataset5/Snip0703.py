def weighted_histogram_filter(img, kernel, kernel_center, percentile_min=0.0, percentile_max=1.0, min_width=1.0):
    def vec(x):
        return np.array(x)

    kernel_min = -kernel_center
    kernel_max = vec(kernel.shape) - kernel_center

    def weighted_histogram_filter_single(idx):
        idx = vec(idx)
        min_index = np.maximum(0, idx + kernel_min)
        max_index = np.minimum(vec(img.shape), idx + kernel_max)
        window_shape = max_index - min_index

        class WeightedElement:
            """
            An element of the histogram, its weight
            and bounds.
            """

            def __init__(self, value, weight):
                self.value: float = value
                self.weight: float = weight
                self.window_min: float = 0.0
                self.window_max: float = 1.0

        values = []
        for window_tup in np.ndindex(tuple(window_shape)):
            window_index = vec(window_tup)
            image_index = window_index + min_index
            centered_kernel_index = image_index - idx
            kernel_index = centered_kernel_index + kernel_center
            element = WeightedElement(img[tuple(image_index)], kernel[tuple(kernel_index)])
            values.append(element)

        def sort_key(x: WeightedElement):
            return x.value

        values.sort(key=sort_key)
        sum = 0
        for i in range(len(values)):
            values[i].window_min = sum
            sum += values[i].weight
            values[i].window_max = sum

        window_min = sum * percentile_min
        window_max = sum * percentile_max
        window_width = window_max - window_min

        if window_width < min_width:
            window_center = (window_min + window_max) / 2
            window_min = window_center - min_width / 2
            window_max = window_center + min_width / 2

            if window_max > sum:
                window_max = sum
                window_min = sum - min_width

            if window_min < 0:
                window_min = 0
                window_max = min_width

        value = 0
        value_weight = 0

        for i in range(len(values)):
            if window_min >= values[i].window_max:
                continue
            if window_max <= values[i].window_min:
                break

            s = max(window_min, values[i].window_min)
            e = min(window_max, values[i].window_max)
            w = e - s

            value += values[i].value * w
            value_weight += w

        return value / value_weight if value_weight != 0 else 0

    img_out = img.copy()

    for index in np.ndindex(img.shape):
        img_out[index] = weighted_histogram_filter_single(index)

    return img_out
