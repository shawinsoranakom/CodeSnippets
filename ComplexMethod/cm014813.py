def test_where(self, sparse_kind, fill_value):

        is_hybrid = False
        if sparse_kind == 'coo':

            def to_sparse(dense):
                return dense.to_sparse(2)

            def set_values(sparse, index, value):
                sparse._values()[index] = value

        elif sparse_kind == 'hybrid_coo':
            is_hybrid = True

            def to_sparse(dense):
                return dense.to_sparse(1)

            def set_values(sparse, index, value):
                sparse._values()[index] = value

        elif sparse_kind == 'csr':

            def to_sparse(dense):
                return dense.to_sparse_csr()

            def set_values(sparse, index, value):
                sparse.values()[index] = value

        else:
            raise AssertionError(f"unexpected sparse_kind: {sparse_kind}")

        mask = torch.tensor([[1, 0, 1, 0, 0],
                             [1, 1, 1, 1, 0],
                             [0, 1, 0, 1, 0],
                             [0, 0, 0, 0, 0],
                             [0, 0, 1, 1, 0],
                             [1, 1, 0, 0, 0]]).to(dtype=bool)
        mask = to_sparse(mask)
        # make some specified mask elements as explicit masked-out masks:
        if is_hybrid:
            set_values(mask, (1, 1), False)
            set_values(mask, (-2, -2), False)
        else:
            set_values(mask, 3, False)
            set_values(mask, -3, False)

        input = torch.tensor([[1, 0, 0, 0, -1],
                              [2, 3, 0, 0, -2],
                              [0, 4, 5, 0, -3],
                              [0, 0, 6, 7, 0],
                              [0, 8, 9, 0, -3],
                              [10, 11, 0, 0, -5]])
        input = to_sparse(input)
        # make specified input elements have zero values:
        if is_hybrid:
            set_values(input, (1, 1), 0)
            set_values(input, (-1, 0), 0)
            F = fill_value
        else:
            set_values(input, 3, 0)
            set_values(input, -3, 0)
            F = 0

        # expected where result:
        Z = 99
        # Z value corresponds to masked-in elements that are not
        # specified in the input and it will be replaced with a zero
        tmp = torch.tensor([[1, F, Z, F, F],
                            [2, F, Z, Z, F],
                            [F, 4, F, Z, F],
                            [0, 0, 0, 0, 0],
                            [F, F, 9, F, F],
                            [Z, 11, F, F, F]])
        tmp = to_sparse(tmp)


        sparse = torch.masked._where(mask, input,
                                     torch.tensor(fill_value, dtype=input.dtype, device=input.device))

        if tmp.layout == torch.sparse_coo:
            expected_sparse = torch.sparse_coo_tensor(
                tmp.indices(),
                torch.where(tmp.values() != Z, tmp.values(), tmp.values().new_full([], 0)),
                input.shape)
            outmask = torch.sparse_coo_tensor(sparse.indices(),
                                              sparse.values().new_full(sparse.values().shape, 1).to(dtype=bool),
                                              sparse.shape)._coalesced_(True)
        elif tmp.layout == torch.sparse_csr:
            expected_sparse = torch.sparse_csr_tensor(
                tmp.crow_indices(),
                tmp.col_indices(),
                torch.where(tmp.values() != Z, tmp.values(), tmp.values().new_full([], 0)),
                input.shape)
            outmask = torch.sparse_csr_tensor(sparse.crow_indices(), sparse.col_indices(),
                                              sparse.values().new_full(sparse.values().shape, 1).to(dtype=bool),
                                              sparse.shape)
        else:
            raise AssertionError("unexpected sparse layout")

        self.assertEqual(sparse, expected_sparse)

        # check invariance:
        #  torch.where(mask.to_dense(), input.to_dense(), fill_value)
        #    == where(mask, input, fill_value).to_dense(fill_value)
        expected = torch.where(mask.to_dense(), input.to_dense(), torch.full(input.shape, F))
        dense = torch.where(outmask.to_dense(), sparse.to_dense(), torch.full(sparse.shape, F))
        self.assertEqual(dense, expected)