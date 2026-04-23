def deserialize(
        self,
        serialized_graph_module: GraphModule,
        serialized_state_dict: dict[str, torch.Tensor] | bytes,
        constants: dict[str, Any] | bytes,
        example_inputs: tuple[tuple[torch.Tensor, ...], dict[str, Any]]
        | bytes
        | None = None,
        symbol_name_to_range: dict[str, symbolic_shapes.ValueRanges] | None = None,
    ) -> Result:
        global _CURRENT_DESERIALIZER
        if _CURRENT_DESERIALIZER is not None:
            raise AssertionError("_CURRENT_DESERIALIZER is already set")
        _CURRENT_DESERIALIZER = self
        try:
            log.debug("\n[deserialize]")
            self.shape_env = symbolic_shapes.ShapeEnv(assume_static_by_default=True)
            self.fake_tensor_mode = FakeTensorMode(
                allow_fallback_kernels=False,
                allow_non_fake_inputs=True,
                shape_env=self.shape_env,
            )
            self.sympy_functions = {
                # all torch.utils._sympy.functions should go here
                # TODO(avik): find a better way to keep this collection in sync;
                # e.g.., `exec('from torch.utils._sympy.functions import *', ...)`
                # would work as long as the public API of that module is complete
                "FloorDiv": torch.utils._sympy.functions.FloorDiv,
                "ModularIndexing": torch.utils._sympy.functions.ModularIndexing,
                "Where": torch.utils._sympy.functions.Where,
                "PythonMod": torch.utils._sympy.functions.PythonMod,
                "Mod": torch.utils._sympy.functions.Mod,
                "CleanDiv": torch.utils._sympy.functions.CleanDiv,
                "CeilToInt": torch.utils._sympy.functions.CeilToInt,
                "FloorToInt": torch.utils._sympy.functions.FloorToInt,
                "CeilDiv": torch.utils._sympy.functions.CeilDiv,
                "LShift": torch.utils._sympy.functions.LShift,
                "RShift": torch.utils._sympy.functions.RShift,
                "PowByNatural": torch.utils._sympy.functions.PowByNatural,
                "FloatPow": torch.utils._sympy.functions.FloatPow,
                "FloatTrueDiv": torch.utils._sympy.functions.FloatTrueDiv,
                "IntTrueDiv": torch.utils._sympy.functions.IntTrueDiv,
                "IsNonOverlappingAndDenseIndicator": torch.utils._sympy.functions.IsNonOverlappingAndDenseIndicator,
                "TruncToFloat": torch.utils._sympy.functions.TruncToFloat,
                "TruncToInt": torch.utils._sympy.functions.TruncToInt,
                "RoundToInt": torch.utils._sympy.functions.RoundToInt,
                "RoundDecimal": torch.utils._sympy.functions.RoundDecimal,
                "ToFloat": torch.utils._sympy.functions.ToFloat,
                "Identity": torch.utils._sympy.functions.Identity,
            }
            self.symbol_name_to_symbol: dict[str, sympy.Symbol] = {}
            self.constants = deserialize_torch_artifact(constants)
            self.signature = self.deserialize_signature(
                serialized_graph_module.signature
            )

            # deserialization does analysis with checks on 0/1, so we create fake range constraints and
            # restore the original range constraints afterwards
            self.symbol_name_to_range = {}
            # we also need to bump unbacked sym[float,int] counters in the
            # shape env to accommodate unbacked symbols in the exported program
            self.unbacked_symbols = set()
            count_unbacked_symfloat, count_unbacked_symint = -1, -1
            unbacked_symfloat_prefix, unbacked_symint_prefix = (
                prefix_str[t] for t in [SymT.UNBACKED_FLOAT, SymT.UNBACKED_INT]
            )
            if symbol_name_to_range:
                for k, vr in symbol_name_to_range.items():
                    lower = vr.lower
                    self.symbol_name_to_range[k] = symbolic_shapes.ValueRanges(
                        _int_to_sympy_int(lower, -int_oo), vr.upper
                    )
                    if k.startswith(unbacked_symfloat_prefix):
                        i = int(k[len(unbacked_symfloat_prefix) :])
                        count_unbacked_symfloat = max(count_unbacked_symfloat, i)
                    elif k.startswith(unbacked_symint_prefix):
                        i = int(k[len(unbacked_symint_prefix) :])
                        count_unbacked_symint = max(count_unbacked_symint, i)

            # TODO(pianpwk): if we can clean up unused symbols in range_constraints,
            # then this logic can just be handled with self.unbacked_symbols alone
            for _ in range(count_unbacked_symfloat + 1):
                self.shape_env.unbacked_symfloat_counter += 1
            for _ in range(count_unbacked_symint + 1):
                self.shape_env.unbacked_symint_counter += 1

            if example_inputs is not None and len(example_inputs) > 0:
                self.example_inputs = deserialize_torch_artifact(example_inputs)
            else:
                self.example_inputs = None
            self.deserialize_graph(serialized_graph_module.graph)

            with _enable_graph_inputs_of_type_nn_module(self.example_inputs):
                module_call_graph = self.deserialize_module_call_graph(
                    serialized_graph_module.module_call_graph
                )
            graph_module = ep._create_graph_module_for_export(self.module, self.graph)
            meta = {}
            if custom := serialized_graph_module.metadata.get("custom"):
                meta["custom"] = json.loads(custom)
            if hasattr(serialized_graph_module, "treespec_namedtuple_fields"):
                meta["treespec_namedtuple_fields"] = {}
                for (
                    type_,
                    fields,
                ) in serialized_graph_module.treespec_namedtuple_fields.items():
                    meta["treespec_namedtuple_fields"][type_] = fields.field_names
            graph_module.meta = meta
            return GraphModuleDeserializer.Result(
                graph_module=graph_module,
                signature=self.signature,
                module_call_graph=module_call_graph,
                names_to_symbols=self.symbol_name_to_symbol,
                state_dict=deserialize_torch_artifact(serialized_state_dict),
                constants=self.constants,
                example_inputs=self.example_inputs,
            )
        finally:
            _CURRENT_DESERIALIZER = None