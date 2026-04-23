def match_block_expr() -> BlockDescriptorOptions | None:
                index_relative_to_xyr_index = sympy_subs(
                    index, {v: t.expr for v, t in self.range_tree_nodes.items()}
                )
                range_trees = self.active_range_trees()

                # Partition the index into subexpressions pertaining to each range tree.
                # For example xindex * 5 + r0_index * 3 is partitioned to
                # (xindex * 5, r0_index * 3).
                index_subexprs = [
                    BlockPatternMatcher.get_subexpr_involving_symbol(
                        index_relative_to_xyr_index, tree.symbol()
                    )
                    for tree in range_trees
                ]

                # Match each range tree's subexpression separately.
                range_symbols = OrderedSet(tree.symbol() for tree in range_trees)
                block_params = BlockParameters()
                for tree, subexpr in zip(range_trees, index_subexprs):
                    # Reject mixed terms, e.g. xindex * r0_index.
                    # NB: the zero expression is allowed, for broadcasting.
                    if len(range_symbols.intersection(subexpr.free_symbols)) > 1:
                        return None

                    # Match the subexpression for this range tree.
                    params = match_block_subexpr(subexpr, tree)
                    if params is None:
                        return None
                    block_params += params

                # Collect leftover terms as a constant offset.
                offset = index_relative_to_xyr_index - sum(index_subexprs)

                # Form the block pointer or TMA descriptor.
                self.filter_masks(mask_vars)

                options_class = (
                    self.block_ptr_options_cls
                    if config.triton.use_block_ptr
                    else self.tensor_descriptor_options_cls
                )
                nonlocal tma_compatibility_checker
                stride_sorter_cls: type[BlockParameters.StrideSorter]
                if config.triton.use_block_ptr:
                    can_lift = False
                    stride_sorter_cls = BlockParameters.IdentityStrideSorter
                else:
                    tma_compatibility_checker = cast(
                        TMACompatibilityChecker, tma_compatibility_checker
                    )
                    can_lift = tma_compatibility_checker.can_lift()

                    if (
                        self.transpose_discontiguous_tensor_descriptors_override
                        is not None
                    ):
                        transpose_contiguous = (
                            self.transpose_discontiguous_tensor_descriptors_override
                        )
                    else:
                        transpose_contiguous = (
                            config.triton.transpose_discontiguous_tensor_descriptor
                        )

                    # For templates:
                    # Only try transpose if we know the output shape
                    # in case we need to transpose the data.
                    if hasattr(self, "template_out_shape"):
                        transpose_contiguous &= copy_shape is not None

                    stride_sorter_cls = (
                        BlockParameters.TensorDecriptorStrideSorter
                        if transpose_contiguous
                        else BlockParameters.IdentityStrideSorter
                    )

                options = options_class.create(
                    params=block_params,
                    constant_offset=offset,
                    range_trees=range_trees,
                    mask_vars=mask_vars,
                    get_max_block=self.max_block,
                    can_lift=can_lift,
                    stride_sorter_cls=stride_sorter_cls,
                )
                if options_class == TensorDescriptorOptions:
                    tma_compatibility_checker = cast(
                        TMACompatibilityChecker, tma_compatibility_checker
                    )
                    if not tma_compatibility_checker.are_block_parameters_compatible(
                        options.params
                    ):
                        return None

                return options