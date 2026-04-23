def wrap_unspecialized_primitive(self, value: Any) -> VariableTracker:
        if self.name in self.tx.output.unspec_variable_map:
            return self.tx.output.unspec_variable_map[self.name]

        wrapped_value = torch.tensor(value)
        if not isinstance(self.get_source(), RandomValueSource):
            install_guard(self.get_source().make_guard(GuardBuilder.TYPE_MATCH))

        options = {"source": self.get_source()}
        options.update({"raw_value": value})

        example_value = wrap_to_fake_tensor_and_record(
            wrapped_value, tx=self.tx, is_tensor=False, source=self.get_source()
        )
        proxy = self.tx.output.root_tracer.create_graph_input(
            re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
            type(wrapped_value),
            example_value,
            source=self.get_source(),
        )
        cache_real_value_when_export(self.tx, proxy, wrapped_value)

        unspec_var = wrap_fx_proxy_cls(
            UnspecializedPythonVariable,
            tx=self.tx,
            proxy=proxy,
            example_value=example_value,
            subclass_type=None,
            **options,
        )
        # type: ignore[assignment]
        self.tx.output.unspec_variable_map[self.name] = unspec_var
        if not is_constant_source(self.get_source()):
            if self.tx.export and not isinstance(self.get_source(), LocalSource):
                raise AssertionError(
                    f"Dynamo attempts to add additional input during export: value={wrapped_value}, source={self.get_source()}"
                )
            fake_tensor_value = None
            if unspec_var.is_python_constant():
                # TODO: when can this happen?
                example_value = unspec_var.as_python_constant()
            else:
                # type: ignore[attr-defined]
                example_value = unspec_var.proxy.node.meta["example_value"]
            assert is_fake(example_value)

            fake_tensor_value = example_value
            # type: ignore[attr-defined]
            assert fake_tensor_value.fake_mode is self.tx.fake_mode, (
                f"fake mode ({fake_tensor_value.fake_mode}) from fake tensor metadata doesn't match mode"
                "({self.tx.fake_mode}) from InstructionTranslator"
            )

            proxy.node.meta["grapharg"] = GraphArg(
                self.get_source(),
                wrapped_value,
                pass_arg_as_tensor=True,
                # type: ignore[arg-type]
                fake_tensor=fake_tensor_value,
                is_tensor=False,
                example_strong_ref=wrapped_value,
            )
        return unspec_var