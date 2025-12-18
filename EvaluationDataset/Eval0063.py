def haralick_descriptors(matrix: np.ndarray) -> list[float]:

    i, j = np.ogrid[0 : matrix.shape[0], 0 : matrix.shape[1]]  

    prod = np.multiply(i, j)
    sub = np.subtract(i, j)

    maximum_prob = np.max(matrix)
    correlation = prod * matrix
    energy = np.power(matrix, 2)
    contrast = matrix * np.power(sub, 2)

    dissimilarity = matrix * np.abs(sub)
    inverse_difference = matrix / (1 + np.abs(sub))
    homogeneity = matrix / (1 + np.power(sub, 2))
    entropy = -(matrix[matrix > 0] * np.log(matrix[matrix > 0]))
  
    return [
        maximum_prob,
        correlation.sum(),
        energy.sum(),
        contrast.sum(),
        dissimilarity.sum(),
        inverse_difference.sum(),
        homogeneity.sum(),
        entropy.sum(),
    ]
