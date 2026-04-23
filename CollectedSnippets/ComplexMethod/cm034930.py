def gen_tgt_perms(self, tgt):
        """Generate shared permutations for the whole batch.
        This works because the same attention mask can be used for the shorter sequences
        because of the padding mask.
        """
        max_num_chars = tgt.shape[1] - 2
        if max_num_chars == 1:
            return paddle.arange(end=3).unsqueeze(axis=0)
        perms = [paddle.arange(end=max_num_chars)] if self.perm_forward else []
        max_perms = math.factorial(max_num_chars)
        if self.perm_mirrored:
            max_perms //= 2
        num_gen_perms = min(self.max_gen_perms, max_perms)
        if max_num_chars < 5:
            if max_num_chars == 4 and self.perm_mirrored:
                selector = [0, 3, 4, 6, 9, 10, 12, 16, 17, 18, 19, 21]
            else:
                selector = list(range(max_perms))
            perm_pool = paddle.to_tensor(
                data=list(permutations(range(max_num_chars), max_num_chars)),
                place=self._device,
            )[selector]
            if self.perm_forward:
                perm_pool = perm_pool[1:]
            perms = paddle.stack(x=perms)
            if len(perm_pool):
                i = self.rng.choice(
                    len(perm_pool), size=num_gen_perms - len(perms), replace=False
                )
                perms = paddle.concat(x=[perms, perm_pool[i]])
        else:
            perms.extend(
                [
                    paddle.randperm(n=max_num_chars)
                    for _ in range(num_gen_perms - len(perms))
                ]
            )
            perms = paddle.stack(x=perms)
        if self.perm_mirrored:
            comp = perms.flip(axis=-1)
            x = paddle.stack(x=[perms, comp])
            perm_2 = list(range(x.ndim))
            perm_2[0] = 1
            perm_2[1] = 0
            perms = x.transpose(perm=perm_2).reshape((-1, max_num_chars))
        bos_idx = paddle.zeros(shape=(len(perms), 1), dtype=perms.dtype)
        eos_idx = paddle.full(
            shape=(len(perms), 1), fill_value=max_num_chars + 1, dtype=perms.dtype
        )
        perms = paddle.concat(x=[bos_idx, perms + 1, eos_idx], axis=1)
        if len(perms) > 1:
            perms[(1), 1:] = max_num_chars + 1 - paddle.arange(end=max_num_chars + 1)
        return perms