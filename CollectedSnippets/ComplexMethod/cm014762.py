def test_jagged_layout_construction_as_nested_tensor(
        self, device, dtype, components_require_grad
    ):
        # NB: as_nested_tensor(tensor_list) doesn't support lists of lists for tensor_list
        for tensor_list in self._get_example_tensor_lists(
            include_list_of_lists=False, include_requires_grad=components_require_grad
        ):
            nt = torch.nested.as_nested_tensor(
                tensor_list, device=device, dtype=dtype, layout=torch.jagged
            )

            # nt.requires_grad=True should be set if at least one component requires grad
            expected_dim = tensor_list[0].dim() + 1
            expected_batch_size = len(tensor_list)
            expected_contiguous = True
            expected_min_seqlen = min(
                (torch.tensor(t) if isinstance(t, list) else t).shape[0]
                for t in tensor_list
            )
            expected_max_seqlen = max(
                (torch.tensor(t) if isinstance(t, list) else t).shape[0]
                for t in tensor_list
            )
            self._validate_nt(
                nt,
                device,
                dtype,
                torch.jagged,
                components_require_grad,
                expected_dim,
                expected_batch_size,
                expected_contiguous,
                expected_min_seqlen,
                expected_max_seqlen,
            )

            # Make sure grads flow back into original tensors for as_nested_tensor()
            if components_require_grad:
                (nt * 2).backward(torch.ones_like(nt))
                for t in tensor_list:
                    if t.requires_grad:
                        self.assertEqual(t.grad, torch.ones_like(t) * 2)
                    else:
                        self.assertTrue(t.grad is None)