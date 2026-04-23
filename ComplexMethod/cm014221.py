def as_python_constant(self) -> object:
        from ..utils import is_pybind11_enum_member

        if isinstance(
            self.value,
            (enum.Enum, torch.DispatchKey, torch._C._functorch.TransformType),
        ) or is_pybind11_enum_member(self.value):
            return self.value

        if self.is_pytree_constant_class and self.source:
            # NOTE pytree constants created in the torch.compile region will
            # NOT be guarded (even though they have a source set)
            return self.value
            # TODO else try reconstructing the object by, e.g., leveraging side
            # effects and `as_python_constant`.

        # Special case for _MaskModWrapper during legacy export: Dynamo creates
        # objects via __new__ without calling __init__, so self.value.fn is unset.
        # Reconstruct from the tracked side-effect attribute instead.
        from torch.nn.attention.flex_attention import _MaskModWrapper

        if isinstance(self.value, _MaskModWrapper):
            from torch._dynamo.symbolic_convert import InstructionTranslator

            tx = InstructionTranslator.current_tx()
            if tx is not None and tx.export:
                fn_vt = tx.output.side_effects.load_attr(self, "fn", deleted_ok=True)
                if fn_vt is not None:
                    # Let as_python_constant() raise the proper exception
                    # (e.g., ClosureConversionError for non-constant closures)
                    fn = fn_vt.as_python_constant()
                    return _MaskModWrapper(fn)

        return super().as_python_constant()