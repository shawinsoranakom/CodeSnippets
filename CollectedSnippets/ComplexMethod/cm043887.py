def build_key_with_indicator(target_dim: str) -> str:
        """Build constraint key with indicator always set, targeting a specific dimension.

        This builds a full key for all dimensions, with the target dimension as wildcard
        and the indicator dimension set to the indicator code (if available).
        This allows querying for available values of the target dimension filtered by indicator.
        """
        key_parts: list[str] = []
        for dim_id in dim_order:
            if dim_id == target_dim:
                # Target dimension gets wildcard - we want to know available values
                key_parts.append("*")
            elif dim_id == country_dim:
                key_parts.append(str(country).replace(",", "+") if country else "*")
            elif dim_id == indicator_dim:
                # Always include indicator code if available
                key_parts.append(indicator_code if indicator_code else "*")
            elif dim_id == freq_dim:
                key_parts.append(str(frequency) if frequency else "*")
            elif dim_id in (transform_dim, unit_dim):
                key_parts.append(
                    str(transform) if transform and transform != "true" else "*"
                )
            elif dim_id in extra_dimensions:
                # Use value from dimension_values if provided
                key_parts.append(extra_dimensions[dim_id])
            else:
                key_parts.append("*")

        return ".".join(key_parts)