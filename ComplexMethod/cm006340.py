def split_if_needed(self, max_url_size: int = MAX_TELEMETRY_URL_SIZE) -> list["ComponentInputsPayload"]:
        """Split payload into multiple chunks if URL size exceeds max_url_size.

        Args:
            max_url_size: Maximum allowed URL length in characters (default: MAX_TELEMETRY_URL_SIZE)

        Returns:
            List of ComponentInputsPayload objects. Single item if no split needed,
            multiple items if payload was split across chunks.
        """
        from lfx.log.logger import logger

        # Calculate current URL size
        current_size = self._calculate_url_size()

        # If fits within limit, return as-is
        if current_size <= max_url_size:
            return [self]

        # Need to split - check if component_inputs is a dict
        if not isinstance(self.component_inputs, dict):
            # If not a dict, return as-is (fail-safe)
            logger.warning(f"component_inputs is not a dict, cannot split: {type(self.component_inputs)}")
            return [self]

        if not self.component_inputs:
            # Empty inputs, return as-is
            return [self]

        # Distribute input fields across chunks
        chunks_data = []
        current_chunk_inputs: dict[str, Any] = {}

        for key, value in self.component_inputs.items():
            # Calculate size if we add this field to current chunk
            test_inputs = {**current_chunk_inputs, key: value}
            test_payload = ComponentInputsPayload(
                component_run_id=self.component_run_id,
                component_id=self.component_id,
                component_name=self.component_name,
                component_inputs=test_inputs,
                chunk_index=0,
                total_chunks=1,
            )
            test_size = test_payload._calculate_url_size()

            # If adding this field exceeds limit, start new chunk
            if test_size > max_url_size and current_chunk_inputs:
                chunks_data.append(current_chunk_inputs)
                # Check if the field by itself exceeds the limit
                single_field_test = ComponentInputsPayload(
                    component_run_id=self.component_run_id,
                    component_id=self.component_id,
                    component_name=self.component_name,
                    component_inputs={key: value},
                    chunk_index=0,
                    total_chunks=1,
                )
                if single_field_test._calculate_url_size() > max_url_size:
                    # Single field is too large - truncate it
                    logger.warning(f"Truncating oversized field '{key}' in component_inputs")
                    truncated_value = self._truncate_value_to_fit(key, value, max_url_size)
                    current_chunk_inputs = {key: truncated_value}
                else:
                    current_chunk_inputs = {key: value}
            elif test_size > max_url_size and not current_chunk_inputs:
                # Single field is too large - truncate it
                logger.warning(f"Truncating oversized field '{key}' in component_inputs")

                # Binary search to find max value length that fits
                truncated_value = self._truncate_value_to_fit(key, value, max_url_size)
                current_chunk_inputs[key] = truncated_value
            else:
                current_chunk_inputs[key] = value

        # Add final chunk
        if current_chunk_inputs:
            chunks_data.append(current_chunk_inputs)

        # Create chunk payloads
        total_chunks = len(chunks_data)
        result = []

        for chunk_index, chunk_inputs in enumerate(chunks_data):
            chunk_payload = ComponentInputsPayload(
                component_run_id=self.component_run_id,
                component_id=self.component_id,
                component_name=self.component_name,
                component_inputs=chunk_inputs,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
            )
            result.append(chunk_payload)

        return result