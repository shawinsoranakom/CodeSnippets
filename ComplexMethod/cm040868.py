def validate_location_constraint(context_region: str, location_constraint: str) -> None:
    if location_constraint:
        if context_region == AWS_REGION_US_EAST_1:
            if (
                not config.ALLOW_NONSTANDARD_REGIONS
                and location_constraint not in BUCKET_LOCATION_CONSTRAINTS
            ):
                raise InvalidLocationConstraint(
                    "The specified location-constraint is not valid",
                    LocationConstraint=location_constraint,
                )
        elif context_region == AWS_REGION_EU_WEST_1:
            if location_constraint not in EU_WEST_1_LOCATION_CONSTRAINTS:
                raise IllegalLocationConstraintException(location_constraint)
        elif context_region != location_constraint:
            raise IllegalLocationConstraintException(location_constraint)
    else:
        if context_region != AWS_REGION_US_EAST_1:
            raise IllegalLocationConstraintException("unspecified")