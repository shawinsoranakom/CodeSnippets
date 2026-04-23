def get_weight_perm(num_bits: int, is_a_8bit: bool = False):
    perm_list: list[int] = []
    if is_a_8bit:
        for i in range(32):
            perm1 = []
            col = i // 4
            for block in [0, 1]:
                for row in [
                    4 * (i % 4),
                    4 * (i % 4) + 1,
                    4 * (i % 4) + 2,
                    4 * (i % 4) + 3,
                    4 * (i % 4 + 4),
                    4 * (i % 4 + 4) + 1,
                    4 * (i % 4 + 4) + 2,
                    4 * (i % 4 + 4) + 3,
                ]:
                    perm1.append(16 * row + col + 8 * block)
            for j in range(2):
                perm_list.extend([p + 512 * j for p in perm1])
    else:
        for i in range(32):
            perm1 = []
            col = i // 4
            for block in [0, 1]:
                for row in [
                    2 * (i % 4),
                    2 * (i % 4) + 1,
                    2 * (i % 4 + 4),
                    2 * (i % 4 + 4) + 1,
                ]:
                    perm1.append(16 * row + col + 8 * block)
            for j in range(4):
                perm_list.extend([p + 256 * j for p in perm1])

    perm = np.array(perm_list)

    if num_bits == 4:
        if is_a_8bit:  # noqa: SIM108
            interleave = np.array([0, 4, 1, 5, 2, 6, 3, 7])
        else:
            interleave = np.array([0, 2, 4, 6, 1, 3, 5, 7])
    elif num_bits == 8:
        if is_a_8bit:  # noqa: SIM108
            interleave = np.array([0, 1, 2, 3])
        else:
            interleave = np.array([0, 2, 1, 3])
    else:
        raise Exception("num_bits must be 4 or 8, got {}".format(num_bits))

    perm = perm.reshape((-1, len(interleave)))[:, interleave].ravel()
    perm = torch.from_numpy(perm)
    return perm