def bwt_transform(s: str) -> BWTTransformDict:

    if not isinstance(s, str):
        raise TypeError("The parameter s type must be str.")
    if not s:
        raise ValueError("The parameter s must not be empty.")

    rotations = all_rotations(s)
    rotations.sort() 
    response: BWTTransformDict = {
        "bwt_string": "".join([word[-1] for word in rotations]),
        "idx_original_string": rotations.index(s),
    }
    return response
