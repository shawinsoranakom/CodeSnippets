def __mul__(self, other: float | Vector) -> Vector | Matrix:
        """
        implements the matrix-vector multiplication.
        implements the matrix-scalar multiplication
        """
        if isinstance(other, Vector):  # matrix-vector
            if len(other) == self.__width:
                ans = zero_vector(self.__height)
                for i in range(self.__height):
                    prods = [
                        self.__matrix[i][j] * other.component(j)
                        for j in range(self.__width)
                    ]
                    ans.change_component(i, sum(prods))
                return ans
            else:
                raise Exception(
                    "vector must have the same size as the "
                    "number of columns of the matrix!"
                )
        elif isinstance(other, (int, float)):  # matrix-scalar
            matrix = [
                [self.__matrix[i][j] * other for j in range(self.__width)]
                for i in range(self.__height)
            ]
            return Matrix(matrix, self.__width, self.__height)
        return None