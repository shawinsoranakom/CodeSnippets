def test_to_numpy_force_argument(self, device) -> None:
        for force in [False, True]:
            for requires_grad in [False, True]:
                for sparse in [False, True]:
                    for conj in [False, True]:
                        data = [[1 + 2j, -2 + 3j], [-1 - 2j, 3 - 2j]]
                        x = torch.tensor(
                            data, requires_grad=requires_grad, device=device
                        )
                        y = x
                        if sparse:
                            if requires_grad:
                                continue
                            x = x.to_sparse()
                        if conj:
                            x = x.conj()
                            y = x.resolve_conj()
                        expect_error = (
                            requires_grad or sparse or conj or device != "cpu"
                        )
                        error_msg = r"Use (t|T)ensor\..*(\.numpy\(\))?"
                        if not force and expect_error:
                            self.assertRaisesRegex(
                                (RuntimeError, TypeError), error_msg, lambda: x.numpy()
                            )
                            self.assertRaisesRegex(
                                (RuntimeError, TypeError),
                                error_msg,
                                lambda: x.numpy(force=False),
                            )
                        elif force and sparse:
                            self.assertRaisesRegex(
                                TypeError, error_msg, lambda: x.numpy(force=True)
                            )
                        else:
                            self.assertEqual(x.numpy(force=force), y)