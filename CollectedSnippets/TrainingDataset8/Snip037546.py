def parse_label(label: str) -> str:
        if not isinstance(label, str):
            raise TypeError(
                f"'{str(label)}' is of type {str(type(label))}, which is not an accepted type."
                " label only accepts: str. Please convert the label to an accepted type."
            )
        return label