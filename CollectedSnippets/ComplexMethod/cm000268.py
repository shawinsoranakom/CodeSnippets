def __mul__(self, other: Matrix | float) -> Matrix:
        if isinstance(other, (int, float)):
            return Matrix(
                [[int(element * other) for element in row] for row in self.rows]
            )
        elif isinstance(other, Matrix):
            if self.num_columns != other.num_rows:
                raise ValueError(
                    "The number of columns in the first matrix must "
                    "be equal to the number of rows in the second"
                )
            return Matrix(
                [
                    [Matrix.dot_product(row, column) for column in other.columns()]
                    for row in self.rows
                ]
            )
        else:
            raise TypeError(
                "A Matrix can only be multiplied by an int, float, or another matrix"
            )