def get_source_by_walking_mro(
        self, tx: "InstructionTranslator", name: str
    ) -> DictGetItemSource:
        assert self.cls_source is not None

        for idx, klass in enumerate(type(self.value).__mro__):
            if name in klass.__dict__:
                descriptor = klass.__dict__[name]

                # Guard that intermediate MRO classes don't shadow this
                # attribute, deduplicating by (id(klass), name) across
                # subclasses that share the same intermediate MRO class.
                # Safe because TYPE_MATCH guards fix the MRO, so the same
                # id(klass) always refers to the same class object.
                for absent_idx in range(1, idx):
                    absent_klass = type(self.value).__mro__[absent_idx]
                    cache_key = (id(absent_klass), name)
                    if cache_key in tx.output.guarded_mro_absent_keys:
                        continue
                    tx.output.guarded_mro_absent_keys.add(cache_key)
                    mro_source = TypeMROSource(self.cls_source)
                    klass_source: Source = GetItemSource(mro_source, absent_idx)
                    dict_source = TypeDictSource(klass_source)
                    install_guard(
                        dict_source.make_guard(
                            functools.partial(GuardBuilder.DICT_NOT_CONTAINS, key=name)
                        )
                    )

                # Guard that the instance __dict__ does not shadow the
                # class attribute.  Skipped for data descriptors (those
                # with __set__, e.g. property) because Python gives data
                # descriptors priority over instance __dict__ in attribute
                # lookup — the instance dict can only be populated by
                # directly writing to obj.__dict__, not via setattr.
                if (
                    self.source
                    and hasattr(self.value, "__dict__")
                    and name not in self.value.__dict__
                    and not hasattr(descriptor, "__set__")
                ):
                    install_guard(
                        self.source.make_guard(
                            functools.partial(
                                GuardBuilder.NOT_PRESENT_IN_GENERIC_DICT, attr=name
                            )
                        )
                    )

                # Reuse the source if we've already resolved the same
                # descriptor object for the same attribute name (e.g. same
                # property reached via different subclasses) to avoid
                # redundant ID_MATCH guards.  We include name in the key
                # because distinct attributes can point to the same object
                # (e.g. a = b = some_obj, or interned small integers).
                cache_key = (id(descriptor), name)
                cache = tx.output.mro_source_cache
                if cache_key in cache:
                    return cache[cache_key]

                if idx != 0:
                    mro_source = TypeMROSource(self.cls_source)
                    klass_source = GetItemSource(mro_source, idx)
                else:
                    klass_source = self.cls_source
                dict_source = TypeDictSource(klass_source)
                out_source = DictGetItemSource(dict_source, name)
                cache[cache_key] = out_source
                return out_source

        unimplemented(
            gb_type="could not find name in object's mro",
            context=f"name={name}, object type={type(self.value)}, mro={type(self.value).__mro__}",
            explanation=f"Could not find name `{name}` in mro {type(self.value).__mro__}",
            hints=[
                f"Ensure the name `{name}` is defined somewhere in {self.value}'s type hierarchy.",
                *graph_break_hints.USER_ERROR,
            ],
        )