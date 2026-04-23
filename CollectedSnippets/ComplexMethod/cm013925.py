def getattr_on_nn_module(
        self,
        source: AttrSource,
        base_guard_manager: GuardManager,
        base_example_value: Any,
        example_value: Any,
        base_source_name: str,
        source_name: str,
        guard_manager_enum: GuardManagerType,
    ) -> GuardManager:
        """
        This tries to avoid calling the expensive nn module custom getattr method by
        checking if the attribute is accessible via __dict__. For attributes that
        are not accessible via __dict__ (like descriptors), we fallback to
        PyObject_GetAttr.

        There are two cases that we optimize for
        1) attributes present directly in __dict__, e.g training.
        2) parameters/buffers/modules - they can be accessed via _parameters,
        _buffers, _modules keys in __dict__. For example, mod.linear can be
        accessed as mod.__dict__["_parameters"]["linear"]

        The most common and expensive case for nn module guards is of type
        mod.submod1.submod2.submod3.training. We avoid the python getattr of nn
        modules by going through the __dict__.
        """

        def getitem_on_dict_mgr(
            mgr: GuardManager,
            key: Any,
            source_name: str,
            base_example_value: Any,
            example_value: Any,
            guard_manager_enum: GuardManagerType,
        ) -> GuardManager:
            if isinstance(mgr, DictGuardManager):
                # Case where the user code relies on key order, e.g.,
                # named_parameters
                index = get_key_index(base_example_value, key)

                # Install the key manager and add equals match guard
                key_source = f"list(dict.keys({source_name}))[{index!r}]"
                mgr.get_key_manager(
                    index=index,
                    source=key_source,
                    example_value=key,
                    guard_manager_enum=GuardManagerType.GUARD_MANAGER,
                ).add_equals_match_guard(key, [f"{key_source} == {key!r}"], None)

                # Install the value manager
                return mgr.get_value_manager(
                    index=index,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
            else:
                return mgr.dict_getitem_manager(
                    key=key,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )

        attr_name = source.member
        mod_dict = base_example_value.__dict__

        all_class_attribute_names: set[str] = set()
        for x in inspect.getmro(base_example_value.__class__):
            all_class_attribute_names.update(x.__dict__.keys())

        accessor_info = NNModuleAttrAccessorInfo(False, None, None)

        if attr_name in mod_dict:
            accessor_info = NNModuleAttrAccessorInfo(True, attr_name, None)
        elif "_parameters" in mod_dict and attr_name in mod_dict["_parameters"]:
            accessor_info = NNModuleAttrAccessorInfo(True, "_parameters", attr_name)
        elif "_buffers" in mod_dict and attr_name in mod_dict["_buffers"]:
            accessor_info = NNModuleAttrAccessorInfo(True, "_buffers", attr_name)
        elif (
            attr_name not in all_class_attribute_names
            and "_modules" in mod_dict
            and attr_name in mod_dict["_modules"]
        ):
            # Check test_attr_precedence test - instance attributes always take precedence unless its an nn.Module.
            accessor_info = NNModuleAttrAccessorInfo(True, "_modules", attr_name)

        if not accessor_info.present_in_generic_dict:
            # The attribute can be accessed by __getattribute__ call, so rely on
            # PyObject_GetAttr
            return base_guard_manager.getattr_manager(
                attr=source.member,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        else:
            assert accessor_info.l1_key
            l1_key = accessor_info.l1_key
            l2_key = accessor_info.l2_key

            # Set source strings for debug info
            mod_dict_source = f"{base_source_name}.__dict__"
            l1_source_name = l2_source_name = None
            l1_value = l2_value = None
            l1_guard_manager_enum = l2_guard_manager_enum = None
            if l2_key:
                l1_source = AttrSource(source.base, l1_key)
                l1_source_name = l1_source.name
                l1_value = mod_dict[l1_key]
                # do not guard on key order for _parameters etc unless the user code
                # actually needs the key order (e.g. calling named_parameters)
                l1_guard_manager_enum = self.get_guard_manager_type(l1_source, l1_value)

                l2_source_name = source_name
                l2_value = example_value
                l2_guard_manager_enum = self.get_guard_manager_type(
                    source, example_value
                )
            else:
                l1_source_name = source_name
                l1_value = example_value
                l1_guard_manager_enum = self.get_guard_manager_type(
                    source, example_value
                )

            # Get __dict__ accessor. No need to guard on dict key order, so use base
            # Guard Manager
            mod_generic_dict_manager = base_guard_manager.get_generic_dict_manager(
                source=mod_dict_source,
                example_value=self._get_generic_dict_manager_example_value(mod_dict),
                guard_manager_enum=GuardManagerType.GUARD_MANAGER,
            )

            l1_mgr = getitem_on_dict_mgr(
                mgr=mod_generic_dict_manager,
                key=l1_key,
                source_name=l1_source_name,
                base_example_value=mod_dict,
                example_value=l1_value,
                guard_manager_enum=l1_guard_manager_enum,
            )

            if l2_key:
                assert l2_source_name is not None and l2_guard_manager_enum is not None
                return getitem_on_dict_mgr(
                    mgr=l1_mgr,
                    key=l2_key,
                    source_name=l2_source_name,
                    base_example_value=l1_value,
                    example_value=l2_value,
                    guard_manager_enum=l2_guard_manager_enum,
                )
            return l1_mgr