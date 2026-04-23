def _assert_interleaved_struct(self, res, base1, base2):
        # base1 and base2 can be Tensors or tuples of Tensors.
        # If they are tuples, res should be a tuple as well.
        # The indexing works as follows for base1, base2 being
        # - tuple, tuple: res[i][j][k][l] = (base1[i][k], base2[j][l])
        # - tuple, Tensor: res[i][k][l] = (base1[i][k], base2[l])
        # - Tensor, tuple: res[i][j][l] = (base1[i], base2[j][l])
        # - Tensor, Tensor: res[k][l] = (base1[k], base2[l])
        if isinstance(base1, torch.Tensor) and isinstance(base2, torch.Tensor):
            self.assertTrue(isinstance(res, torch.Tensor))
            self.assertEqual(res.size(), base1.size() + base2.size())
        elif isinstance(base1, tuple) and isinstance(base2, torch.Tensor):
            self.assertTrue(isinstance(res, tuple))
            self.assertEqual(len(res), len(base1))
            for el_res, el_base1 in zip(res, base1):
                self.assertTrue(isinstance(el_res, torch.Tensor))
                self.assertTrue(isinstance(el_base1, torch.Tensor))
                self.assertEqual(el_res.size(), el_base1.size() + base2.size())
        elif isinstance(base1, torch.Tensor) and isinstance(base2, tuple):
            self.assertTrue(isinstance(res, tuple))
            self.assertEqual(len(res), len(base2))
            for el_res, el_base2 in zip(res, base2):
                self.assertTrue(isinstance(el_res, torch.Tensor))
                self.assertTrue(isinstance(el_base2, torch.Tensor))
                self.assertEqual(el_res.size(), base1.size() + el_base2.size())
        elif isinstance(base1, tuple) and isinstance(base2, tuple):
            self.assertTrue(isinstance(res, tuple))
            self.assertEqual(len(res), len(base1))
            for el_res, el_base1 in zip(res, base1):
                self.assertTrue(isinstance(el_res, tuple))
                self.assertEqual(len(res), len(base2))
                for el_el_res, el_base2 in zip(el_res, base2):
                    self.assertTrue(isinstance(el_el_res, torch.Tensor))
                    self.assertTrue(isinstance(el_base2, torch.Tensor))
                    self.assertEqual(
                        el_el_res.size(), el_base1.size() + el_base2.size()
                    )
        else:
            # Wrong bases
            raise RuntimeError(
                "The bases given to `_assert_interleaved_struct` don't have"
                " the right structure."
            )