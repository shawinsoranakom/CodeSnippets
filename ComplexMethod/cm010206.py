def deserialize(
        self,
        exported_program: ExportedProgram,
        state_dict: dict[str, torch.Tensor] | bytes,
        constants: dict[str, torch.Tensor] | bytes,
        example_inputs: tuple[tuple[torch.Tensor, ...], dict[str, Any]]
        | bytes
        | None = None,
        *,
        _unsafe_skip_version_check=False,
    ) -> ep.ExportedProgram:
        if not isinstance(exported_program, ExportedProgram):
            raise AssertionError(
                f"expected ExportedProgram, got {type(exported_program).__name__}"
            )
        version = exported_program.schema_version

        # TODO(zhxchen17) blocked on thrift schema refactor
        if version.major != SCHEMA_VERSION[0] and not (
            version.major == 0 and version.minor == 0
        ):
            if not _unsafe_skip_version_check:
                raise SerializeError(
                    f"Serialized schema version {exported_program.schema_version} "
                    f"does not match our current schema version {SCHEMA_VERSION}."
                )

        symbol_name_to_range = {
            k: symbolic_shapes.ValueRanges(
                _int_to_sympy_int(v.min_val, -int_oo),
                _int_to_sympy_int(v.max_val, int_oo),
            )
            for k, v in exported_program.range_constraints.items()
        }
        res = GraphModuleDeserializer().deserialize(
            exported_program.graph_module,
            state_dict,
            constants,
            example_inputs,
            symbol_name_to_range,
        )
        range_constraints = self.deserialize_range_constraints(
            symbol_name_to_range,
            res.names_to_symbols,
        )

        result = ep.ExportedProgram(
            root=res.graph_module,
            graph=res.graph_module.graph,
            graph_signature=res.signature,
            state_dict=res.state_dict,  # type: ignore[arg-type]
            range_constraints=range_constraints,
            module_call_graph=res.module_call_graph,
            example_inputs=res.example_inputs,
            constants=res.constants,
            verifiers=[load_verifier(v) for v in exported_program.verifiers],
        )
        result._guards_code = exported_program.guards_code
        log.debug("\n[deserialize]: %s", result)
        return result