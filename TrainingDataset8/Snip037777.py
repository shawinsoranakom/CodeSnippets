def select_dg_to_save(self, invoked_id: str, acting_on_id: str) -> str:
        """Select the id of the DG that this message should be invoked on
        during message replay.

        See Note [DeltaGenerator method invocation]

        invoked_id is the DG the st function was called on, usually `st._main`.
        acting_on_id is the DG the st function ultimately runs on, which may be different
        if the invoked DG delegated to another one because it was in a `with` block.
        """
        if len(self._seen_dg_stack) > 0 and acting_on_id in self._seen_dg_stack[-1]:
            return acting_on_id
        else:
            return invoked_id