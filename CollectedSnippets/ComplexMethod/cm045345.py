def has_nested_base_model(cls: type[IsDataclass]) -> bool:
    for f in fields(cls):
        field_type = f.type
        # Resolve forward references and other annotations
        origin = get_origin(field_type)
        args = get_args(field_type)

        # If the field type is directly a subclass of BaseModel
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            return True

        # If the field type is a generic type like List[BaseModel], Tuple[BaseModel, ...], etc.
        if origin is not None and args:
            for arg in args:
                # Recursively check the argument types
                if isinstance(arg, type) and issubclass(arg, BaseModel):
                    return True
                elif get_origin(arg) is not None:
                    # Handle nested generics like List[List[BaseModel]]
                    if has_nested_base_model_in_type(arg):
                        return True
        # Handle Union types
        elif args:
            for arg in args:
                if isinstance(arg, type) and issubclass(arg, BaseModel):
                    return True
                elif get_origin(arg) is not None:
                    if has_nested_base_model_in_type(arg):
                        return True
    return False