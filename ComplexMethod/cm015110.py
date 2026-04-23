def _test_coalesce(t):
            tc = t.coalesce()
            self.assertEqual(tc.to_dense(), t.to_dense())
            self.assertTrue(tc.is_coalesced())
            # Our code below doesn't work when nnz is 0, because
            # then it's a 0D tensor, not a 2D tensor.
            if t._nnz() == 0:
                self.assertEqual(t._indices(), tc._indices())
                self.assertEqual(t._values(), tc._values())
                return tc

            value_map: dict[Any, Any] = {}
            for idx, val in zip(t._indices().t(), t._values()):
                idx_tup = tuple(idx.tolist())
                if idx_tup in value_map:
                    value_map[idx_tup] += val
                else:
                    value_map[idx_tup] = val.clone() if isinstance(val, torch.Tensor) else val

            new_indices = sorted(value_map.keys())
            _new_values = [value_map[idx] for idx in new_indices]
            if t._values().ndimension() < 2:
                new_values = t._values().new(_new_values)
            else:
                new_values = torch.stack(_new_values)

            new_indices = t._indices().new(new_indices).t()
            tg = t.new(new_indices, new_values, t.size())

            self.assertEqual(tc._indices(), tg._indices())
            self.assertEqual(tc._values(), tg._values())

            if t.is_coalesced():
                self.assertEqual(tc._indices(), t._indices())
                self.assertEqual(tc._values(), t._values())