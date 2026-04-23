def gen_sizes_matmul(self, x_dim, y_dim=4, matrix_size=4, batch_size=3):
        """
        Generates sequences of tuples (x, y) of with size(x) = x_dim and
        size(y) <= y_dim that are compatible wrt. matmul
        """
        if x_dim < 1:
            raise AssertionError(f"x_dim should be >= 1, got {x_dim}")
        if y_dim < 2:
            raise AssertionError(f"y_dim should be >= 2, got {y_dim}")
        x = x_dim
        for y in range(1, y_dim + 1):
            for batch, mn in product(product(range(batch_size), repeat=max(x - 2, y - 2, 0)),
                                     product(range(matrix_size), repeat=min(y, 2))):
                if x == 1:
                    size_x = mn[:1]
                    size_y = batch + mn
                    yield size_x, size_y
                else:
                    for k in range(matrix_size):
                        size_x = (k,) + mn[:1]
                        if x > 2:
                            size_x = batch[-(x - 2):] + size_x
                        size_y = mn
                        if y > 2:
                            size_y = batch[-(y - 2):] + size_y
                        yield size_x, size_y