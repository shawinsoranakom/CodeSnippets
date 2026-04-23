def _validate_handles(self, source, target) -> None:
        if self.target_handle.input_types is None:
            # Backward compatibility: old flows may have Data/DataFrame types
            self.valid_handles = types_compatible(
                self.source_handle.output_types, [self.target_handle.type] if self.target_handle.type else []
            )
        elif self.target_handle.type is None:
            # ! This is not a good solution
            # This is a loop edge
            # If the target_handle.type is None, it means it's a loop edge
            # and we should check if the source_handle.output_types is not empty
            # and if the target_handle.input_types is empty or if any of the source_handle.output_types
            # is in the target_handle.input_types
            self.valid_handles = bool(self.source_handle.output_types) and (
                not self.target_handle.input_types
                or types_compatible(self.source_handle.output_types, self.target_handle.input_types)
            )

        elif self.source_handle.output_types is not None:
            # Backward compatibility: old flows may have Data/DataFrame types
            self.valid_handles = types_compatible(
                self.source_handle.output_types, self.target_handle.input_types
            ) or types_compatible(
                self.source_handle.output_types, [self.target_handle.type] if self.target_handle.type else []
            )

        if not self.valid_handles:
            logger.debug(self.source_handle)
            logger.debug(self.target_handle)
            msg = f"Edge between {source.display_name} and {target.display_name} has invalid handles"
            raise ValueError(msg)