def _generate_arn():
        # some custom hacks
        if shape.name in custom_arns:
            return custom_arns[shape.name]

        max_len = shape.metadata.get("max") or math.inf
        min_len = shape.metadata.get("min") or 0

        pattern = shape.metadata.get("pattern")
        if pattern:
            # FIXME: also conforming to length may be difficult
            pattern = sanitize_arn_pattern(pattern)
            pattern = sanitize_pattern(pattern)
            arn = rstr.xeger(pattern)
        else:
            arn = DEFAULT_ARN

        # if there's a value set for the region, replace with a randomly picked region
        # TODO: splitting the ARNs here by ":" sometimes fails for some reason (e.g. or dynamodb for some reason)
        arn_parts = arn.split(":")
        if len(arn_parts) >= 4:
            region = arn_parts[3]
            if region:
                # TODO: check service in ARN and try to get the actual region for the service
                regions = botocore.session.Session().get_available_regions("lambda")
                picked_region = random.choice(regions)
                arn_parts[3] = picked_region
                arn = ":".join(arn_parts)

        if len(arn) > max_len:
            arn = arn[:max_len]

        if len(arn) < min_len or len(arn) > max_len:
            raise ValueError(
                f"generated arn {arn} for shape {shape.name} does not match constraints {shape.metadata}"
            )

        return arn