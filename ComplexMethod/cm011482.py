def _update_placements(obj: Any):
        if isinstance(obj, DTensorSpec):
            unique_placements.update(obj.placements)
        elif isinstance(obj, OpStrategy):
            if len(obj.strategies) != 1:
                raise AssertionError
            unique_placements.update(obj.strategies[0].output_spec.placements)
        elif isinstance(obj, TupleStrategy):
            for child in obj.children:
                _update_placements(child)
        elif isinstance(obj, (list, tuple)):
            for child in obj:
                _update_placements(child)