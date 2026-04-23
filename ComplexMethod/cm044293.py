def _get_generic_types(cls, type_: type, items: list) -> list[str]:
        """Unpack generic types recursively.

        Parameters
        ----------
        type_ : type
            Type to unpack.
        items : list
            List to store the unpacked types.

        Returns
        -------
        List[str]
            List of unpacked type names.

        Examples
        --------
        Union[List[str], Dict[str, str], Tuple[str]] -> ["List", "Dict", "Tuple"]
        """
        if hasattr(type_, "__args__"):
            origin = get_origin(type_)
            if origin is Union or origin is UnionType:
                for arg in type_.__args__:
                    cls._get_generic_types(arg, items)
            elif (
                isinstance(origin, type)
                and origin is not Annotated
                and (name := getattr(type_, "_name", getattr(origin, "__name__", None)))
            ):
                items.append(name)
                for arg in type_.__args__:
                    cls._get_generic_types(arg, items)

        return items