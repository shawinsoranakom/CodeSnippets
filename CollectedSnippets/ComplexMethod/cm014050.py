def codegen_update_mutated(
        self, cg: PyCodegen, log_side_effects: bool = False
    ) -> None:
        side_effect_messages: list[str] = []

        # NOTE: should only be called once per VT - only if a side effect actually gets codegen'd!
        def _maybe_log_side_effect(var: VariableTracker) -> None:
            if config.side_effect_replay_policy != "silent" and log_side_effects:
                msg = self._format_side_effect_message(var)
                side_effect_messages.append(msg)

        suffixes = []
        for var in self._get_modified_vars():
            # When replay_side_effects=False, only update variables with TempLocalSource
            if not config.replay_side_effects and not isinstance(
                var.source, TempLocalSource
            ):
                continue
            if isinstance(var, variables.ListVariable):
                # old[:] = new
                cg(var, allow_cache=False)  # Don't codegen via source
                cg(var.source)  # type: ignore[attr-defined]
                cg.extend_output(
                    [
                        cg.create_load_const(None),
                        cg.create_load_const(None),
                        create_instruction("BUILD_SLICE", arg=2),
                    ]
                )
                suffixes.append([create_instruction("STORE_SUBSCR")])
                _maybe_log_side_effect(var)
            elif isinstance(var, variables.lists.DequeVariable):
                # For limited maxlen, the order of operations matter for side
                # effect, but we currently don't track the order, so no support.
                if not var.maxlen.is_constant_none():
                    unimplemented(
                        gb_type="Side effect on existing deque with limited maxlen",
                        context="",
                        explanation="This is not supported.",
                        hints=[
                            "Don't use a deque with `maxlen` specified.",
                        ],
                    )

                # old.extend(new), this runs last
                cg(var.source)
                cg.load_method("extend")
                cg(var, allow_cache=False)  # Don't codegen via source
                suffixes.append(
                    [
                        *create_call_method(1),
                        create_instruction("POP_TOP"),
                    ]
                )

                # old.clear(), this runs first
                cg(var.source)
                cg.load_method("clear")
                suffixes.append(
                    [
                        *create_call_method(0),
                        create_instruction("POP_TOP"),
                    ]
                )
                _maybe_log_side_effect(var)

            elif isinstance(var, (variables.ConstDictVariable, variables.SetVariable)):
                # Reconstruct works as follow:
                # (1) Skip codegen if there are no new items
                # (2) codegen(...) each pair of key/value
                # (3) create a new dictionary with the pairs of key/values above
                # (4) clear the original dictionary
                #   + only if a key was removed from the input dict
                # (5) update the original dictionary with the dict created in (2)

                if var.has_new_items():
                    cg(var.source)  # type: ignore[attr-defined]
                    cg.load_method("update")
                    cg(var, allow_cache=False)  # Don't codegen via source

                    if var.should_reconstruct_all:
                        cg(var.source)  # type: ignore[attr-defined]
                        cg.load_method("clear")

                    suffixes.append(
                        [
                            *create_call_method(1),  # update
                            create_instruction("POP_TOP"),
                        ]
                    )

                    if var.should_reconstruct_all:
                        # clear will appear before "update" as the suffixes are
                        # applied in reverse order.
                        suffixes.append(
                            [
                                *create_call_method(0),  # clear
                                create_instruction("POP_TOP"),
                            ]
                        )
                    _maybe_log_side_effect(var)

            elif isinstance(
                var, variables.torch_function.TorchFunctionModeStackVariable
            ):
                # Needed in the finally block for stack restoration
                cg.add_push_null(
                    lambda: cg.load_import_from(
                        utils.__name__, "get_torch_function_mode_stack"
                    )
                )
                cg.call_function(0, False)
                name = variables.torch_function.get_prev_stack_var_name()
                cg.code_options["co_varnames"] += (name,)
                cg.append_output(create_instruction("STORE_FAST", argval=name))
                cg.add_push_null(
                    lambda: cg.load_import_from(
                        utils.__name__, "set_torch_function_mode_stack"
                    )
                )

                cg.foreach(var.symbolic_stack)
                cg.append_output(
                    create_instruction("BUILD_LIST", arg=len(var.symbolic_stack))
                )
                cg.call_function(1, False)
                cg.append_output(create_instruction("POP_TOP"))
                _maybe_log_side_effect(var)

            elif isinstance(var, variables.CellVariable) and var.local_name is not None:
                # Emit more readable and performant bytecode.
                # TODO generalize this for cells created during inlining.
                if var in self.store_attr_mutations:
                    contents_var = self.load_cell(var)
                    cg(contents_var)
                    suffixes.append([cg.create_store_deref(var.local_name)])
                    _maybe_log_side_effect(var)

            elif self.is_attribute_mutation(var):
                # FrozenDataClassVariable attributes were emitted in
                # codegen_save_tempvars right after __new__. Skip here to
                # avoid double-emitting.
                if isinstance(var.mutation_type, AttributeMutationNew) and isinstance(
                    var, variables.FrozenDataClassVariable
                ):
                    continue

                if (
                    isinstance(
                        var,
                        variables.UserDefinedDictVariable,
                    )
                    and self.is_modified(
                        var._base_vt  # pyrefly: ignore[bad-argument-type]
                    )
                    and var._base_vt.has_new_items(  # pyrefly: ignore[union-attr,missing-attribute]
                    )
                ):
                    # Do dict related update manually here. The store_attr
                    # mutations will be applied later.
                    varname_map = {}
                    for name in _manual_dict_setitem.__code__.co_varnames:
                        varname_map[name] = cg.tx.output.new_var()

                    try:
                        mro_index = type(var.value).__mro__.index(
                            collections.OrderedDict
                        )
                    except ValueError:
                        mro_index = type(var.value).__mro__.index(dict)

                    cg.extend_output(
                        [
                            create_instruction("LOAD_CONST", argval=mro_index),
                            create_instruction(
                                "STORE_FAST", argval=varname_map["mro_index"]
                            ),
                        ]
                    )

                    cg(var.source)  # type: ignore[attr-defined]
                    cg.extend_output(
                        [
                            create_instruction(
                                "STORE_FAST", argval=varname_map["dict_to"]
                            )
                        ]
                    )

                    # Reconstruct all items — _manual_dict_setitem clears
                    # dict_to first, so we need every key/value, not just
                    # the ones that differ from original_items.
                    var._base_vt.should_reconstruct_all = True  # type: ignore[union-attr]
                    cg(var._base_vt, allow_cache=False)  # Don't codegen via source
                    cg.extend_output(
                        [
                            create_instruction(
                                "STORE_FAST", argval=varname_map["dict_from"]
                            )
                        ]
                    )

                    dict_update_insts = bytecode_from_template(
                        _manual_dict_setitem, varname_map=varname_map
                    )

                    suffixes.append(
                        [
                            *dict_update_insts,
                            create_instruction("POP_TOP"),
                        ]
                    )
                    _maybe_log_side_effect(
                        var._base_vt  # pyrefly: ignore[bad-argument-type]
                    )
                elif isinstance(
                    var,
                    variables.UserDefinedListVariable,
                ) and self.is_modified(
                    var._base_vt  # pyrefly: ignore[bad-argument-type]
                ):
                    # Update the list to the updated items. Be careful in
                    # calling the list methods and not the overridden methods.
                    varname_map = {}
                    for name in _manual_list_update.__code__.co_varnames:
                        varname_map[name] = cg.tx.output.new_var()

                    cg(var.source)  # type: ignore[attr-defined]
                    cg.extend_output(
                        [
                            create_instruction(
                                "STORE_FAST", argval=varname_map["list_to"]
                            )
                        ]
                    )

                    cg(var._base_vt, allow_cache=False)  # Don't codegen via source
                    cg.extend_output(
                        [
                            create_instruction(
                                "STORE_FAST", argval=varname_map["list_from"]
                            )
                        ]
                    )

                    list_update_insts = bytecode_from_template(
                        _manual_list_update, varname_map=varname_map
                    )

                    suffixes.append(
                        [
                            *list_update_insts,
                            create_instruction("POP_TOP"),
                        ]
                    )
                    _maybe_log_side_effect(
                        var._base_vt  # pyrefly: ignore[bad-argument-type]
                    )

                # Applying mutations involves two steps: 1) Push all
                # reconstructed objects onto the stack.  2) Call STORE_ATTR to
                # apply the mutations.
                #
                # Dynamo must ensure that mutations are applied in the same
                # order as in the original program. Therefore, two reverse
                # operations occur below.
                #
                # The first reverse operation concerns `suffixes`. We apply
                # suffixes in reverse order due to the way Python handles the
                # stack. In Step 1, we push all reconstructed objects onto the
                # stack, but the item at the top of the stack refers to the last
                # attribute in the mutation order. If not fixed, this will apply
                # the mutations of attributes in the reverse order.  To account
                # for this reversal, we iterate through the mutable attributes
                # in reverse order.
                side_effect_occurred = False
                for name, value in reversed(
                    self.store_attr_mutations.get(var, {}).items()
                ):
                    if isinstance(var, variables.NewGlobalVariable):
                        cg.tx.output.update_co_names(name)
                        cg(value)
                        assert isinstance(var.source, GlobalSource)  # type: ignore[attr-defined]
                        suffixes.append(
                            [create_instruction("STORE_GLOBAL", argval=name)]
                        )
                        side_effect_occurred = True
                    elif isinstance(value, variables.DeletedVariable):
                        if isinstance(
                            var.mutation_type, AttributeMutationExisting
                        ) and hasattr(getattr(var, "value", None), name):
                            cg.tx.output.update_co_names(name)
                            cg(var.source)
                            suffixes.append(
                                [create_instruction("DELETE_ATTR", argval=name)]
                            )
                            side_effect_occurred = True
                    elif isinstance(
                        var, variables.UserDefinedObjectVariable
                    ) and var.should_skip_descriptor_setter(name):
                        cg.add_push_null(
                            lambda: cg.load_import_from(
                                utils.__name__, "object_setattr_ignore_descriptor"
                            )
                        )
                        cg(var.source)  # type: ignore[attr-defined]
                        cg(variables.ConstantVariable(name))
                        cg(value)
                        suffixes.append(
                            [
                                *create_call_function(3, False),
                                create_instruction("POP_TOP"),
                            ]
                        )
                        side_effect_occurred = True
                    elif (
                        isinstance(var, variables.UserDefinedObjectVariable)
                        and var.needs_slow_setattr()
                    ):
                        # __setattr__ is defined on this object, so call object.__setattr__ directly
                        cg.load_import_from("builtins", "object")
                        cg.load_method("__setattr__")
                        cg(var.source)  # type: ignore[attr-defined]
                        cg(variables.ConstantVariable(name))
                        cg(value)
                        suffixes.append(
                            [*create_call_method(3), create_instruction("POP_TOP")]
                        )
                        side_effect_occurred = True
                    else:
                        cg.tx.output.update_co_names(name)
                        cg(value)
                        cg(var)
                        suffixes.append([create_instruction("STORE_ATTR", argval=name)])
                        side_effect_occurred = True

                if side_effect_occurred:
                    _maybe_log_side_effect(var)
            elif isinstance(var, variables.ListIteratorVariable):
                for _ in range(var.index):
                    cg.add_push_null(
                        lambda: cg.load_import_from(utils.__name__, "iter_next")
                    )
                    cg(var.source)  # type: ignore[attr-defined]
                    cg.call_function(1, False)
                    cg.pop_top()
                _maybe_log_side_effect(var)
            elif isinstance(var, variables.CountIteratorVariable):
                for _ in range(var.advance_count):
                    cg.add_push_null(
                        lambda: cg.load_import_from(utils.__name__, "iter_next")
                    )
                    cg(var.source)  # type: ignore[attr-defined]
                    cg.call_function(1, False)
                    cg.pop_top()
                _maybe_log_side_effect(var)
            elif isinstance(var, variables.RandomVariable):
                # set correct random seed state
                def gen_fn() -> None:
                    cg(var.source)  # type: ignore[attr-defined]
                    cg.load_attr("setstate")

                cg.add_push_null(gen_fn)
                cg(var.wrap_state(var.random.getstate()))

                suffixes.append(
                    [
                        *create_call_function(1, False),  # setstate
                        create_instruction("POP_TOP"),
                    ]
                )
                _maybe_log_side_effect(var)
            else:
                raise AssertionError(type(var))

        # do all the actual mutations at the very end to handle dependencies
        for suffix in reversed(suffixes):
            cg.extend_output(suffix)

        # Send batched structured trace for all side effects in this compilation
        if log_side_effects and side_effect_messages:
            self._emit_side_effect_messages(side_effect_messages)