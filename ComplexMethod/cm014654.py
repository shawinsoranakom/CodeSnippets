def _annotation_type_to_stable_str(self, t, sig_str, recursive: bool = False):
        if t is inspect.Signature.empty:
            return ""

        # Forward ref
        if isinstance(t, str):
            # Normalize "X | None" string annotations to Optional format
            if t.endswith(" | None"):
                inner = t[: -len(" | None")]
                result = f"Optional[{inner}]"
                return result if recursive else f"'{result}'"
            if recursive:
                return t
            else:
                return f"'{t}'"
        if hasattr(typing, "ForwardRef") and isinstance(t, typing.ForwardRef):
            return t.__forward_arg__
        if hasattr(typing, "_ForwardRef") and isinstance(t, typing._ForwardRef):
            return t.__forward_arg__

        mapping = self._trivial_mappings.get(t, None)
        if mapping:
            return mapping

        # Handle types with contained types
        contained = getattr(t, "__args__", None) or []

        # Callables contain a bare List for arguments
        contained = t if isinstance(t, list) else contained

        # Python 3.8 puts type vars into __args__ for unbound types such as Dict
        if all(isinstance(ct, typing.TypeVar) for ct in contained):
            contained = []

        contained_type_annots = [
            self._annotation_type_to_stable_str(ct, sig_str, True) for ct in contained
        ]
        contained_type_str = (
            f'[{", ".join(contained_type_annots)}]'
            if len(contained_type_annots) > 0
            else ""
        )

        origin = getattr(t, "__origin__", None)
        if origin is None:
            # Unbound types don't have `__origin__` in some Python versions, so fix that up here.
            origin = t if t in self._UNBOUND_TYPES else origin

        if origin in {tuple, tuple}:
            return f"Tuple{contained_type_str}"
        if origin == typing.Union or isinstance(t, types.UnionType):
            # Annoying hack to detect Optional
            if len(contained) == 2 and (contained[0] is type(None)) ^ (
                contained[1] is type(None)
            ):
                not_none_param = (
                    contained[0] if contained[0] is not type(None) else contained[1]
                )
                return f"Optional[{self._annotation_type_to_stable_str(not_none_param, sig_str, True)}]"
            return f"Union{contained_type_str}"
        if origin in {dict, dict}:
            return f"Dict{contained_type_str}"
        if origin in {list, list}:
            return f"List{contained_type_str}"
        if origin in {type, type}:
            return f"Type{contained_type_str}"
        if isinstance(t, typing.Callable):
            if len(contained) > 0 and contained[0] is not Ellipsis:
                return f'Callable[[{", ".join(contained_type_annots[:-1])}], {contained_type_annots[-1]}]'
            else:
                return f'Callable{contained_type_str}'

        if t is ArgumentT:
            # ArgumentT is a TypeVar bound to torch.fx.node.Argument
            return f'torch.fx.node.Argument{contained_type_str}'

        raise RuntimeError(f'Unrecognized type {t} used in BC-compatible type signature {sig_str}.'
                           f'Please add support for this type and confirm with the '
                           f'FX team that your signature change is valid.')

        raise RuntimeError(
            f"Unrecognized type {t} used in BC-compatible type signature {sig_str}."
            f"Please add support for this type and confirm with the "
            f"FX team that your signature change is valid."
        )