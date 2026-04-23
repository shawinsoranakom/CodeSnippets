def _convert_to_string(x):
        """Sanitize the data for the table."""
        # pylint: disable=import-outside-toplevel
        from numpy import isnan

        if isinstance(x, (float, int)) and not isnan(x):
            return x
        if isinstance(x, dict):
            return ", ".join([str(v) for v in x.values()])
        if isinstance(x, list):
            if all(isinstance(i, dict) for i in x):
                return ", ".join(
                    str(", ".join([str(v) for v in i.values()])) for i in x
                )
            return ", ".join([str(i) for i in x])

        return (
            str(x)
            .replace("[", "")
            .replace("]", "")
            .replace("'{", "")
            .replace("}'", "")
            .replace("nan", "")
        )