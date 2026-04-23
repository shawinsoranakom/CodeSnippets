def unpack_int4(packed, orig_len, axis=0, dtype="int8"):
    """Unpack a packed int4 back to an int8 tensor in the range [-8, 7].

    This function reverses the packing performed by `pack_int4`, restoring
    the original int8 tensor (values in the range [-8, 7]) from a packed int8
    tensor where each element contains two int4 values (one in the lower nibble,
    one in the upper nibble).

    The function restores the original axis order and removes any
    padding that was added during packing.

    Args:
        packed: An int8 tensor containing packed int4 values along the
            specified axis. Each int8 value encodes two int4 values.
        orig_len: The original (unpadded) length of the axis that was
            packed. This is used to remove any padding that may have
            been added during packing to ensure an even number of rows.
        axis: The axis along which the tensor was packed. Defaults to 0.
        dtype: The data type of the input and unpacked tensor. Can be
            `"int8"` or `"uint8"`. Defaults to `"int8"`.

    Returns:
        unpacked: An int8 tensor with the same shape as the original
            (unpacked) tensor, with values in the range [-8, 7].

    Example:

    ```python
    >>> import numpy as np
    >>> from keras.quantizers import pack_int4, unpack_int4

    # Example with axis=0
    # Original array has shape (3, 2)
    >>> original_array = np.array([[-3, 7], [2, -8], [1, 0]], dtype=np.int8)

    # Pack the array along axis 0. Since the length of axis 0 (3) is
    # odd, it will be padded to a length of 4. The packed array will
    # have a shape of (ceil(3/2), 2) = (2, 2).
    >>> packed, packed_shape, orig_len = pack_int4(original_array, axis=0)
    >>> print("Packed array:\n", packed)
    Packed array:
    [[  45 -121]
    [   1    0]]

    # Now, unpack the array back to its original form
    >>> unpacked = unpack_int4(packed, orig_len, axis=0)
    >>> print("Unpacked array:\n", unpacked)
    Unpacked array:
    [[-3  7]
    [ 2 -8]
    [ 1  0]]
    >>> np.allclose(original_array, unpacked)
    True

    # Example with axis=1
    # Original array has shape (2, 3)
    >>> original_array = np.array([[-3, 7, 2], [-8, 1, 0]], dtype=np.int8)

    # Pack along axis 1. Length of axis 1 (3) is padded to 4.
    # The new shape is (2, ceil(3/2)) = (2, 2).
    >>> packed, packed_shape, orig_len = pack_int4(original_array, axis=1)
    >>> print("Packed array:\n", packed)
    Packed array:
    [[ 125   2]
    [  24   0]]

    # Unpack the array
    >>> unpacked = unpack_int4(packed, orig_len, axis=1)
    >>> print("Unpacked array:\n", unpacked)
    Unpacked array:
    [[-3  7  2]
    [-8  1  0]]
    >>> np.allclose(original_array, unpacked)
    True
    ```
    """
    if dtype not in ("int8", "uint8"):
        raise ValueError(
            f"Expected dtype to be 'int8' or 'uint8', but got '{dtype}'."
        )

    if backend.standardize_dtype(packed.dtype) not in ("int8", "uint8"):
        raise TypeError(
            f"Expected int8 or uint8 tensor for unpacking, got {packed.dtype}"
        )

    def to_signed(x):
        """Converts unpacked nibbles [0, 15] to signed int4 [-8, 7].

        Uses a branchless XOR approach: (x ^ 8) - 8
        This maps: 0->0, 1->1, ..., 7->7, 8->-8, 9->-7, ..., 15->-1
        """
        dtype_x = backend.standardize_dtype(x.dtype)
        eight = ops.cast(8, dtype_x)
        return ops.subtract(ops.bitwise_xor(x, eight), eight)

    rank = getattr(packed.shape, "rank", None) or len(packed.shape)
    if axis < 0:
        axis += rank

    # Fast path for axis==0 (common case in Dense layers)
    if axis == 0 and rank == 2:
        mask = ops.array(0x0F, dtype=packed.dtype)
        low_unpacked = ops.bitwise_and(packed, mask)
        high_unpacked = ops.bitwise_and(ops.right_shift(packed, 4), mask)

        if dtype == "int8":
            low_unpacked = to_signed(low_unpacked)
            high_unpacked = to_signed(high_unpacked)

        low_final = ops.cast(low_unpacked, dtype)
        high_final = ops.cast(high_unpacked, dtype)

        # Interleave along axis 0 and reshape
        stacked = ops.stack([low_final, high_final], axis=1)
        unpacked = ops.reshape(stacked, (-1,) + tuple(ops.shape(packed)[1:]))

        # Remove padding and return
        return unpacked[:orig_len, ...]

    # General case
    perm = [axis] + [i for i in range(rank) if i != axis]
    inv_perm = [perm.index(i) for i in range(rank)]
    transposed = ops.transpose(packed, perm)

    # 1. Split nibbles.
    mask = ops.array(0x0F, dtype=packed.dtype)
    low = ops.bitwise_and(transposed, mask)
    high = ops.bitwise_and(ops.right_shift(transposed, 4), mask)

    # 2. Conditionally convert to signed.
    if dtype == "int8":
        low = to_signed(low)
        high = to_signed(high)

    low = ops.cast(low, dtype)
    high = ops.cast(high, dtype)

    # 3. Interleave and reshape.
    stacked = ops.stack([low, high], axis=1)
    unpacked = ops.reshape(stacked, (-1,) + tuple(ops.shape(transposed)[1:]))

    # 4. Remove padding and restore original layout.
    unpacked = unpacked[:orig_len, ...]
    unpacked = ops.transpose(unpacked, inv_perm)

    return unpacked