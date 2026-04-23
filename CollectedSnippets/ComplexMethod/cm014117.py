def wrap_listlike(
        self, value: Union[tuple[Any, ...], list[Any], odict_values, NamedTuple]
    ) -> VariableTracker:
        if config.specialize_int and type(value) is torch.Size:
            self.install_guards(GuardBuilder.CONSTANT_MATCH)
            return ConstantVariable.create(value=value)

        # One can index a tensor with a list/tuple. Therefore, we need to
        # have a stricter match.
        self.install_guards(GuardBuilder.SEQUENCE_LENGTH)

        # Tuples are immutable objects, so we should mark its items static. This
        # avoids wrapping of tuple items as symints. This helps for nn module
        # attributes like conv2d strides, dilations.
        if (
            istype(value, tuple)
            and all(ConstantVariable.is_literal(item) for item in value)
            and self.source.guard_source.is_unspecialized_nn_module()
        ):
            self.install_guards(GuardBuilder.CONSTANT_MATCH)
            return TupleVariable([ConstantVariable.create(item) for item in value])

        output = [
            LazyVariableTracker.create(
                item,
                source=GetItemSource(self.get_source(), i),
            )
            for i, item in enumerate(value)
        ]

        maybe_gm = self.tx.output.local_scope.get("self")
        if isinstance(
            self.source, LocalSource
        ) and self.source.local_name in get_locals_to_steal(maybe_gm):
            # The input tensor list to dynamo from compiled autograd may contain activations
            # which are freed as they are used in inductor. Dynamo's default behavior is to
            # lift all tensors to the graph inputs, but this will cause dynamo to hold an
            # extra reference to the activation tensors and increase peak memory usage.
            # To allow freeing ASAP, we keep the list as graph argument to the dynamo output
            # graph, and unpack it locally.
            # e.g. instead of `def forward(self, L_inputs_0_, L_inputs_1_, ...):`, we have
            # `def forward(self, L_inputs_):`
            source = self.source
            assert isinstance(value, list)
            tensor_list_proxy = self.tx.output.root_tracer.create_graph_input(
                re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
                type(value),
                value,
                source=source,
            )
            tensor_list_proxy.node.meta["steal_arg"] = True

            list_variable = wrap_fx_proxy_cls(
                target_cls=TensorVariable,
                tx=self.tx,
                proxy=tensor_list_proxy,
                example_value=value,
                subclass_type=None,
                source=source,
            )

            # Apply relevant logic from `VariableTracker.build(value[i])`
            # (except for the `create_graph_input` stuff).
            guards = []
            # type: ignore[attr-defined]
            for i, tensor_variable in enumerate(list_variable.items):
                source_i = GetItemSource(base=source, index=i, index_is_slice=False)
                # access unpacked tensor from this list instead of from a lifted arg
                self.tx.output.input_source_to_var[source_i] = tensor_variable
                tensor_variable.proxy.node.meta["tensor_dict"] = _extract_tensor_dict(
                    value[i]
                )
                guard = functools.partial(
                    GuardBuilder.TENSOR_MATCH, value=TensorWeakRef(value[i])
                )
                guards.append(source_i.make_guard(guard))

            install_guard(*guards, skip=1)

            grapharg = GraphArg(
                source,
                value,
                pass_arg_as_tensor=False,
                fake_tensor=None,
                is_tensor=False,
            )
            tensor_list_proxy.node.meta["grapharg"] = grapharg

            # The following is very important for maintaining the "python object
            # <==> variable tracker" 1-to-1 mapping, which is mainly handled via
            # `side_effects`. Note that constructing `tensor_variable` above
            # already adds it to graph arg, but we never registered it with
            # `side_effects`. The preemptive `realize` calls here basically
            # does that registration (at the end of `self.__call__`).
            #
            # A slightly cleaner alternative is to register the
            # `tensor_variable`s above with `side_effects` directly, and just
            # return the `list_variable`, but that breaks some tensor-subclass
            # related tests like `test_inputs_aliasing_bytecode_stack_restore`,
            # because `tensor_variable` is constructed via
            # `handle_traced_output`, which doesn't really expect/handle tensor
            # subclass.
            #
            # Eventually, we expect to fix remove all of these by having Dynamo
            # auto-boxing inputs to the compiled graph, see
            # https://github.com/pytorch/pytorch/issues/153701.
            for vt in output:
                vt.realize()
        # type: ignore[arg-type]
        result = BaseListVariable.cls_for_instance(value)(output, source=self.source)
        if istype(value, (list, collections.deque)):
            return self.tx.output.side_effects.track_mutable(value, result)
        return result