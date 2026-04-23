def _clean_string_values(value: Any) -> Any:
        """Convert double quotes in string values to single quotes and fix type references.

        Parameters
        ----------
        value : Any
            The value to clean

        Returns
        -------
        Any
            The cleaned value
        """
        if isinstance(value, str):
            # Fix fully qualified Data type references
            value = re.sub(
                r"list\[openbb_core\.provider\.abstract\.data\.Data\]",
                "list[Data]",
                value,
            )
            value = re.sub(
                r"openbb_core\.provider\.abstract\.data\.Data", "Data", value
            )

            # Clean up Union types
            if "Union[" in value:
                try:
                    # Extract types from Union
                    types_str = value[value.find("[") + 1 : value.rfind("]")]
                    # Split types and clean them up
                    types = [t.strip() for t in types_str.split(",")]
                    # Use a set to handle unique types and maintain order for display
                    unique_types = sorted(list(set(types)))
                    # Rebuild the string with " | " separator
                    value = " | ".join(unique_types)
                except Exception:  # pylint: disable=broad-except  # noqa
                    pass

            # Handle Literal types specifically
            if (
                "Literal[" in value
                and "]" in value
                and "'" not in value
                and '"' not in value
            ):
                # Extract the content between Literal[ and ]
                start_idx = value.find("Literal[") + len("Literal[")
                end_idx = value.rfind("]")
                if start_idx < end_idx:
                    content = value[start_idx:end_idx]
                    # Add single quotes around each value
                    values = [f"'{v.strip()}'" for v in content.split(",")]
                    # Reconstruct the Literal type
                    return f"Literal[{', '.join(values)}]"

            value = re.sub(r"\bDict\b", "dict", value)
            value = re.sub(r"\bList\b", "list", value)

            return value.replace('"', "'")

        if isinstance(value, dict):
            return {
                k: ReferenceGenerator._clean_string_values(v) for k, v in value.items()
            }

        if isinstance(value, list):
            return [ReferenceGenerator._clean_string_values(item) for item in value]

        return value