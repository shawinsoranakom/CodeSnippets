def validate_region_and_factor(cls, values):
        """Validate region and factor combination."""
        region = values.get("region", "america")
        factor = factors_dict.get(values.get("factor", "3_factors"), "")
        frequency = values.get("frequency", "")

        if factor and factor in ["st_reversal", "lt_reversal"] and region != "america":
            raise ValueError(
                f"Invalid region, '{region}', for factor '{factor}'. Only 'america' is supported."
            )

        if region and region not in list(FACTOR_REGION_MAP):
            raise ValueError(
                f"Invalid region: '{region}'. "
                + "Valid regions are: "
                + ", ".join(FACTOR_REGION_MAP.keys())
            )

        regional_factors = FACTOR_REGION_MAP[region]

        if factor not in regional_factors.get("factors", {}):
            raise ValueError(
                f"Invalid factor: '{factor}' for region: '{region}'. "
                + "Valid factors are: "
                + ", ".join(regional_factors.get("factors", {}).keys())
            )

        if frequency:
            intervals = regional_factors.get("intervals", {}).get(factor, {})
            if frequency not in list(intervals):
                raise ValueError(
                    f"Invalid frequency: '{frequency}' for factor: '{factor}'"
                    + f" in region: '{region}'. "
                    + "Valid frequencies are: "
                    + ", ".join(intervals.keys())
                )

        return values