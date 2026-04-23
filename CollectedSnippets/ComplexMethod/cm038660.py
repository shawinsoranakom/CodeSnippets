def _pack_binary_embeddings(
    float_embeddings: list[list[float]],
    signed: bool,
) -> list[list[int]]:
    """Bit-pack float embeddings: positive -> 1, negative -> 0.

    Each bit is shifted left by ``7 - idx%8``, and every 8 bits are packed
    into one byte.
    """
    result: list[list[int]] = []
    for embedding in float_embeddings:
        dim = len(embedding)
        if dim % 8 != 0:
            raise ValueError(
                "Embedding dimension must be a multiple of 8 for binary "
                f"embedding types, but got {dim}."
            )
        packed_len = dim // 8
        packed: list[int] = []
        byte_val = 0
        for idx, value in enumerate(embedding):
            bit = 1 if value >= 0 else 0
            byte_val += bit << (7 - idx % 8)
            if (idx + 1) % 8 == 0:
                if signed:
                    byte_val -= _UNSIGNED_TO_SIGNED_DIFF
                packed.append(byte_val)
                byte_val = 0
        assert len(packed) == packed_len
        result.append(packed)
    return result