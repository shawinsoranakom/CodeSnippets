def handle_aliasing_and_mutation(info: torch._C.Argument, arg: Any) -> None:
            # Assertions to make sure we didn't mismatch args
            if isinstance(info.type, torch.ListType):
                assert isinstance(arg, (list, tuple)), type(arg)
            if library_utils.is_tensor_like_type(info.type):
                # PyTorch also accepts None and scalar types for args marked as "Tensor".
                # We're not going to check all of them here.
                assert not isinstance(arg, (tuple, list))

            if arg is None:
                return
            if info.alias_info is None:
                return

            def add_alias(t: IRNode) -> None:
                self.alias_names.append(t.get_name())
                assert info.alias_info is not None
                if info.alias_info.is_write:
                    self.mutation_outputs.append(
                        MutationOutput(NoneLayout(device=t.get_device()), t, self)
                    )

            if library_utils.is_tensorlist_like_type(info.type):
                if arg is not None:
                    for optional_tensor_arg in arg:
                        add_alias(optional_tensor_arg)
            else:
                assert library_utils.is_tensor_like_type(info.type)

                add_alias(arg)