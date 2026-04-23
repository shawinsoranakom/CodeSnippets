def validate_chokepoint(cls, v):
        """Validate the chokepoint parameter."""
        if not v:
            return None

        if isinstance(v, str):
            if "," in v:
                chokepoints = v.split(",")
                for chokepoint in chokepoints:
                    if chokepoint not in list(
                        CHOKEPOINTS_NAME_TO_ID
                    ) and chokepoint not in list(CHOKEPOINTS_NAME_TO_ID.values()):
                        raise OpenBBError(
                            ValueError(
                                f"Invalid chokepoint name: {chokepoint} -> "
                                f"Expected one of {list(CHOKEPOINTS_NAME_TO_ID)}"
                                " - or chokepointN, where N is a number between 1 and 24"
                            )
                        )

                return ",".join(chokepoints) if chokepoints else None

            if (
                v
                and v not in CHOKEPOINTS_NAME_TO_ID
                and v not in list(CHOKEPOINTS_NAME_TO_ID.values())
            ):
                raise OpenBBError(
                    ValueError(
                        f"Invalid chokepoint name: {v} -> "
                        f"Expected one of {list(CHOKEPOINTS_NAME_TO_ID)}"
                        " - or chokepointN, where N is a number between 1 and 24"
                    )
                )

            return (
                v
                if v in CHOKEPOINTS_NAME_TO_ID
                or v in list(CHOKEPOINTS_NAME_TO_ID.values())
                else None
            )

        if isinstance(v, list):
            chokepoints = []
            for d in v:
                if d in CHOKEPOINTS_NAME_TO_ID:
                    chokepoints.append(CHOKEPOINTS_NAME_TO_ID[d])
                elif d in list(CHOKEPOINTS_NAME_TO_ID.values()):
                    chokepoints.append(d)

            return ",".join(chokepoints) if chokepoints else None

        raise OpenBBError(
            ValueError(
                f"Invalid chokepoint value: {v} -> "
                f"Expected a string or a list of strings from {list(CHOKEPOINTS_NAME_TO_ID)}."
                " - or chokepointN, where N is a number between 1 and 24"
            )
        )