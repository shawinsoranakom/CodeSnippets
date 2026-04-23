def test_jagged_layout_construction_nested_tensor(
        self, device, dtype, requires_grad, components_require_grad
    ):
        for tensor_list in self._get_example_tensor_lists(
            include_list_of_lists=True, include_requires_grad=components_require_grad
        ):
            nt = torch.nested.nested_tensor(
                tensor_list,
                device=device,
                dtype=dtype,
                layout=torch.jagged,
                requires_grad=requires_grad,
            )

            expected_dim = torch.as_tensor(tensor_list[0]).dim() + 1
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
                requires_grad,
                expected_dim,
                expected_batch_size,
                expected_contiguous,
                expected_min_seqlen,
                expected_max_seqlen,
            )

            # Make sure grads -don't- flow back into original tensors for nested_tensor()
            if requires_grad:
                (nt * 2).backward(torch.ones_like(nt))
            for t in tensor_list:
                t = t if isinstance(t, torch.Tensor) else torch.as_tensor(t)
                self.assertTrue(t.grad is None)