def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        # Allow skipping of empty hook dict guards on inbuilt nn modules
        if name in (
            "_backward_hooks",
            "_backward_pre_hooks",
            "_forward_hooks_with_kwargs",
            "_forward_hooks",
            "_forward_pre_hooks_with_kwargs",
            "_forward_pre_hooks",
        ):
            # For empty hooks, make an EMPTY_NN_MODULE_HOOKS_DICT. This allows us to control the installation of empty
            # hooks guard via skip_nnmodule_hook_guards
            if not tx.output.side_effects.has_pending_mutation_of_attr(self, name):
                hooks_dict = getattr(self.value, name)
                if isinstance(hooks_dict, dict) and len(hooks_dict) == 0:
                    if self.source:
                        hooks_source = AttrSource(self.source, name)
                        install_guard(
                            hooks_source.make_guard(
                                GuardBuilder.EMPTY_NN_MODULE_HOOKS_DICT
                            )
                        )
                    return variables.ConstDictVariable({})

        # For non-empty hook dicts, one way is to just fallback to VariableTracker.build() and create a ConstDictVariable.
        # However, ConstDictVariable guards on keys. This can cause recompiles when the same hook is installed for
        # different nn module instances, because the key keeps changing (look more into RemovableHandle to understand why
        # key changes - also related https://github.com/pytorch/pytorch/issues/125836). Here, we carefully craft a
        # NNModuleHooksDictVariable (a subclass of ConstDictVariable) to avoid any guard on the keys.
        if (
            self.source
            and name
            in (
                "_forward_pre_hooks_with_kwargs",
                "_forward_pre_hooks",
                "_forward_hooks_with_kwargs",
                "_forward_hooks",
            )
            and not tx.output.side_effects.has_pending_mutation_of_attr(self, name)
        ):
            hooks_dict = getattr(self.value, name)
            hooks_dict_source = AttrSource(self.source, name)
            install_guard(hooks_dict_source.make_guard(GuardBuilder.SEQUENCE_LENGTH))
            tx.output.guard_on_key_order.add(hooks_dict_source)

            def build_key_value(
                i: int, k: Any, v: Any
            ) -> tuple[VariableTracker, VariableTracker]:
                # Make key sourceless to avoid any guard on it
                key = VariableTracker.build(tx, k)

                # Instead of using dict[key] to access the value, use a dict[dict.keys()[index]] to access the
                # value. This removes the reliance on the actual key value.
                source_key = ConstDictKeySource(hooks_dict_source, i)
                source_value = DictGetItemSource(hooks_dict_source, source_key)
                value = LazyVariableTracker.create(v, source_value)
                return key, value

            result = dict(
                build_key_value(i, k, v)
                for i, k, v in enumerate_items_with_dict_position(hooks_dict)
            )

            return variables.NNModuleHooksDictVariable(
                result, type(hooks_dict), source=hooks_dict_source
            )
        return super().var_getattr(tx, name)