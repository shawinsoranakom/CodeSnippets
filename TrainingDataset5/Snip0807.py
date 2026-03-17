def circular_convolution(self) -> list[float]:
    length_first_signal = len(self.first_signal)
    length_second_signal = len(self.second_signal)

    max_length = max(length_first_signal, length_second_signal)

    matrix = [[0] * max_length for i in range(max_length)]

    if length_first_signal < length_second_signal:
        self.first_signal += [0] * (max_length - length_first_signal)
    elif length_first_signal > length_second_signal:
        self.second_signal += [0] * (max_length - length_second_signal)
    for i in range(max_length):
        rotated_signal = deque(self.second_signal)
        rotated_signal.rotate(i)
        for j, item in enumerate(rotated_signal):
            matrix[i][j] += item

    final_signal = np.matmul(np.transpose(matrix), np.transpose(self.first_signal))

    return [float(round(i, 2)) for i in final_signal]
