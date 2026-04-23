def dynamic_getattr(
        self, tx: "InstructionTranslator", name: str
    ) -> VariableTracker:
        fake_val = self.proxy.node.meta["example_value"]
        # For getattrs on tensors without sources,
        # we can do better than the default (creating a GetAttrVariable)
        # if:
        # (1) the tensor is a traceable tensor subclass
        # (2) We are getattr'ing an inner tensor from that subclass
        if not self.source and is_traceable_wrapper_subclass(fake_val):
            attrs, _ctx = fake_val.__tensor_flatten__()
            proxy = getattr(self.as_proxy(), name)
            example_value = getattr(fake_val, name)
            if name in attrs:
                # attrs returned from tensor_flatten are always tensors or opaques
                assert isinstance(example_value, (torch.Tensor, OpaqueBase))
                from .builder import wrap_fx_proxy

                return wrap_fx_proxy(tx=tx, proxy=proxy, example_value=example_value)
            elif is_opaque_reference_type(type(example_value)):
                fake_script_obj = torch._library.fake_class_registry.maybe_to_fake_obj(
                    tx.output.fake_mode, example_value
                )
                return TorchScriptObjectVariable.create(proxy, fake_script_obj)
            elif isinstance(
                example_value,
                torch._library.fake_class_registry.FakeScriptObject,
            ):
                return TorchScriptObjectVariable.create(proxy, example_value)
            # any other attributes on the subclass (that are not methods)
            # are assumed to be constant metadata.
            elif not callable(example_value):
                return VariableTracker.build(tx, example_value)

        if not (self.source and self.source.subguards_allowed()):
            raise NotImplementedError

        # For local source, we associate the real value. We use this real value
        # for implementing getattr fallthrough on the variable tracker base class.

        # Note - this scope construction is mirrored in guards
        # A subsequent PR will introduce a util.
        scope = {"L": tx.output.local_scope, "G": tx.output.global_scope}
        try:
            # We raise in case we get a typerror bug w/ SuperSource.
            # SuperSource has bugs in it atm, and can produce code like
            # eval("super(L['mod'].model.model.encoder.embed_positions.forward__class__,
            # L['mod'].model.model.encoder.embed_positions)", scope)
            # Which is incorrect, and violates the invariant that all sources should be eval()-able against the scope.
            _input_associated_real_value = eval(self.source.name, scope)
        except Exception as exc:
            raise NotImplementedError from exc

        if _input_associated_real_value is None:
            raise NotImplementedError

        if object_has_getattribute(_input_associated_real_value):
            raise NotImplementedError

        if get_custom_getattr(_input_associated_real_value):
            raise NotImplementedError

        try:
            real_value = getattr(_input_associated_real_value, name)
        except AttributeError:
            raise_observed_exception(
                AttributeError,
                tx,
                args=[
                    f"'{type(_input_associated_real_value).__name__}' object has no attribute '{name}'"
                ],
            )

        attr_source = AttrSource(self.source, name)

        # Typically we'd want to use variable builder here
        # but unfortunately id(real_value.__self__) is not id(<original value>)
        if is_bound_tensor_method(real_value):
            # No need to install the guard because its a bound tensor method
            from .misc import GetAttrVariable

            return GetAttrVariable(
                self, name, source=attr_source, py_type=type(real_value)
            )

        install_guard(
            self.source.make_guard(functools.partial(GuardBuilder.HASATTR, attr=name))
        )
        return VariableTracker.build(tx, real_value, attr_source)