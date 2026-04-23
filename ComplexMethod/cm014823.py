def _test_wrapper_subclass_aliasing(self, op, args, kwargs):
        def to_subclass(t: torch.Tensor):
            return TwoTensor(t, t.clone())

        result_ref = op(*args, **kwargs)

        args_subclass = pytree.tree_map_only(torch.Tensor, to_subclass, args)
        kwargs_subclass = pytree.tree_map_only(torch.Tensor, to_subclass, kwargs)

        result_test = op(*args_subclass, **kwargs_subclass)

        args_ref_flat = pytree.arg_tree_leaves(*args, **kwargs)
        args_ref_flat_tensors = [
            x for x in args_ref_flat if isinstance(x, torch.Tensor)
        ]

        args_test_flat = pytree.tree_leaves((args_subclass, kwargs_subclass))
        args_test_flat_tensors = [
            x for x in args_test_flat if isinstance(x, torch.Tensor)
        ]

        result_ref_flat = pytree.tree_leaves(result_ref)
        result_ref_flat_tensors = [
            x for x in result_ref_flat if isinstance(x, torch.Tensor)
        ]

        result_test_flat = pytree.tree_leaves(result_test)
        result_test_flat_tensors = [
            x for x in result_test_flat if isinstance(x, torch.Tensor)
        ]

        for o_ref, o_test in zip(result_ref_flat_tensors, result_test_flat_tensors):
            for a_ref, a_test in zip(args_ref_flat_tensors, args_test_flat_tensors):
                out_is_inpt = o_ref is a_ref
                if out_is_inpt:
                    self.assertTrue(o_test is a_test)

                out_aliases_inpt = StorageWeakRef(
                    o_ref.untyped_storage()
                ) == StorageWeakRef(a_ref.untyped_storage())
                if out_aliases_inpt:
                    self.assertTrue(
                        StorageWeakRef(o_test.untyped_storage())
                        == StorageWeakRef(a_test.untyped_storage())
                    )
                else:
                    self.assertFalse(
                        StorageWeakRef(o_test.untyped_storage())
                        == StorageWeakRef(a_test.untyped_storage())
                    )