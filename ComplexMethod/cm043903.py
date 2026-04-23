def build_key_up_to(target_dim: str) -> str:
            """Build constraint key up to (and including) target dimension."""
            key_parts: list[str] = []
            countries = self.country.split(",") if self.country else []  # type: ignore  # pylint: disable=E1101
            countries_str = (
                "*"
                if countries in ["*", "all"]
                else "+".join([c.upper() for c in countries])
            )

            for dim_id in dim_order:
                if dim_id == target_dim:
                    key_parts.append("*")
                    break
                if dim_id == country_dim:
                    key_parts.append(countries_str if countries_str else "*")
                elif dim_id == indicator_dim:
                    # Use all indicator codes for this dataflow
                    key_parts.append(
                        "+".join(indicator_codes) if indicator_codes else "*"
                    )
                elif dim_id == freq_dim:
                    freq_map = {
                        "annual": "A",
                        "quarter": "Q",
                        "month": "M",
                        "day": "D",
                    }
                    freq_val = freq_map.get(str(self.frequency).lower(), self.frequency)
                    key_parts.append(str(freq_val) if self.frequency else "*")
                elif dim_id == transform_dim:
                    key_parts.append(str(self.transform) if self.transform else "*")
                else:
                    key_parts.append("*")
            return ".".join(key_parts)