def strassen(matrix1: list, matrix2: list) -> list:
    """
    >>> strassen([[2,1,3],[3,4,6],[1,4,2],[7,6,7]], [[4,2,3,4],[2,1,1,1],[8,6,4,2]])
    [[34, 23, 19, 15], [68, 46, 37, 28], [28, 18, 15, 12], [96, 62, 55, 48]]
    >>> strassen([[3,7,5,6,9],[1,5,3,7,8],[1,4,4,5,7]], [[2,4],[5,2],[1,7],[5,5],[7,8]])
    [[139, 163], [121, 134], [100, 121]]
    """
    if matrix_dimensions(matrix1)[1] != matrix_dimensions(matrix2)[0]:
        msg = (
            "Unable to multiply these matrices, please check the dimensions.\n"
            f"Matrix A: {matrix1}\n"
            f"Matrix B: {matrix2}"
        )
        raise Exception(msg)
    dimension1 = matrix_dimensions(matrix1)
    dimension2 = matrix_dimensions(matrix2)

    if dimension1[0] == dimension1[1] and dimension2[0] == dimension2[1]:
        return [matrix1, matrix2]

    maximum = max(*dimension1, *dimension2)
    maxim = int(math.pow(2, math.ceil(math.log2(maximum))))
    new_matrix1 = matrix1
    new_matrix2 = matrix2

    # Adding zeros to the matrices to convert them both into square matrices of equal
    # dimensions that are a power of 2
    for i in range(maxim):
        if i < dimension1[0]:
            for _ in range(dimension1[1], maxim):
                new_matrix1[i].append(0)
        else:
            new_matrix1.append([0] * maxim)
        if i < dimension2[0]:
            for _ in range(dimension2[1], maxim):
                new_matrix2[i].append(0)
        else:
            new_matrix2.append([0] * maxim)

    final_matrix = actual_strassen(new_matrix1, new_matrix2)

    # Removing the additional zeros
    for i in range(maxim):
        if i < dimension1[0]:
            for _ in range(dimension2[1], maxim):
                final_matrix[i].pop()
        else:
            final_matrix.pop()
    return final_matrix