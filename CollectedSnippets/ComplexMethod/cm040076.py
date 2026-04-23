def _validate_inputs(self, inputs, mask=None):
        """Validates arguments of the call method."""
        class_name = self.__class__.__name__
        if not isinstance(inputs, list):
            raise ValueError(
                f"{class_name} layer must be called on a list of inputs, "
                "namely [query, value] or [query, value, key]. "
                f"Received: inputs={inputs}."
            )
        if len(inputs) < 2 or len(inputs) > 3:
            raise ValueError(
                f"{class_name} layer accepts inputs list of length 2 or 3, "
                "namely [query, value] or [query, value, key]. "
                f"Received length: {len(inputs)}."
            )
        if mask is not None:
            if not isinstance(mask, list):
                raise ValueError(
                    f"{class_name} layer mask must be a list, "
                    f"namely [query_mask, value_mask]. Received: mask={mask}."
                )
            if len(mask) < 2 or len(mask) > 3:
                raise ValueError(
                    f"{class_name} layer accepts mask list of length 2 or 3. "
                    f"Received: inputs={inputs}, mask={mask}."
                )