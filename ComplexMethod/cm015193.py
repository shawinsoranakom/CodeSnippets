def _compare_expected_and_result(self, expected, result, mechanism):
        if mechanism == "make_functional":
            expected = zip(*expected)
            expected = tuple(torch.stack(shards) for shards in expected)
            for r, e in zip(result, expected):
                self.assertEqual(r, e, atol=0, rtol=1.5e-3)
        else:
            if mechanism != "functional_call":
                raise AssertionError(
                    f"Expected mechanism 'functional_call', got '{mechanism}'"
                )
            expected = {
                k: tuple(d[k] for d in expected) for k, v in expected[0].items()
            }
            expected = {k: torch.stack(shards) for k, shards in expected.items()}
            for key in result:
                self.assertEqual(result[key], expected[key], atol=0, rtol=1.5e-3)