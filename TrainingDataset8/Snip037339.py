def _parent_block_types(self) -> Iterable[str]:
        """Iterate all the block types used by this DeltaGenerator and all
        its ancestor DeltaGenerators.
        """
        current_dg: Optional[DeltaGenerator] = self
        while current_dg is not None:
            if current_dg._block_type is not None:
                yield current_dg._block_type
            current_dg = current_dg._parent