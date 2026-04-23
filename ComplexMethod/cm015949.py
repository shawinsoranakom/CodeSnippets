def _scaled_dot_attn_ref(
            Q,
            K,
            V,
            dims,
            unseen_mask=None,
            key_padding_mask=None,
            average_attn_weights=average_attn_weights,
        ):
            """Numpy-based reference implementation of scaled dot attention
            for testing"""

            QKT = _batchmatmul(
                Q,
                np.transpose(K, axes=[0, 1, 3, 2])
                / np.sqrt(dims[3], dtype=np.float32),  # divide by sqrt(d_head)
            )
            b1, b2, s1, s2 = QKT.shape
            if unseen_mask is not None or key_padding_mask is not None:
                # assert s1 == s2
                for i in range(b1):
                    for j in range(b2):
                        for m in range(s1):
                            for n in range(s2):
                                if unseen_mask is not None and unseen_mask[m][n] == 0:
                                    QKT[i, j, m, n] = -np.inf
                                if (
                                    key_padding_mask is not None
                                    and key_padding_mask[i][n]
                                ):
                                    QKT[i, j, m, n] = -np.inf

            reference = _softmax(QKT)
            ref_attn_weight = reference
            if average_attn_weights:
                ref_attn_weight = np.sum(ref_attn_weight, axis=1) / b2
            reference = _batchmatmul(reference, V)
            return reference, ref_attn_weight