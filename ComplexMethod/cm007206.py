def create_state_model(model_name: str = "State", *, validate: bool = True, **kwargs) -> type:
    """Create a dynamic Pydantic state model based on the provided keyword arguments.

    This function generates a Pydantic model class with fields corresponding to the
    provided keyword arguments. It can handle various types of field definitions,
    including callable methods (which are converted to properties), FieldInfo objects,
    and type-default value tuples.

    Args:
        model_name (str, optional): The name of the model. Defaults to "State".
        validate (bool, optional): Whether to validate the methods when converting
                                   them to properties. Defaults to True.
        **kwargs: Keyword arguments representing the fields of the model. Each argument
                  can be a callable method, a FieldInfo object, or a tuple of (type, default).

    Returns:
        type: The dynamically created Pydantic state model class.

    Raises:
        ValueError: If the provided field value is invalid or cannot be processed.

    Examples:
        >>> from lfx.components.io import ChatInput
        >>> from lfx.components.io.ChatOutput import ChatOutput
        >>> from pydantic import Field
        >>>
        >>> chat_input = ChatInput()
        >>> chat_output = ChatOutput()
        >>>
        >>> # Create a model with a method from a component
        >>> StateModel = create_state_model(method_one=chat_input.message_response)
        >>> state = StateModel()
        >>> assert state.method_one is UNDEFINED
        >>> chat_input.set_output_value("message", "test")
        >>> assert state.method_one == "test"
        >>>
        >>> # Create a model with multiple components and a Pydantic Field
        >>> NewStateModel = create_state_model(
        ...     model_name="NewStateModel",
        ...     first_method=chat_input.message_response,
        ...     second_method=chat_output.message_response,
        ...     my_attribute=Field(None)
        ... )
        >>> new_state = NewStateModel()
        >>> new_state.first_method = "test"
        >>> new_state.my_attribute = 123
        >>> assert new_state.first_method == "test"
        >>> assert new_state.my_attribute == 123
        >>>
        >>> # Create a model with tuple-based field definitions
        >>> TupleStateModel = create_state_model(field_one=(str, "default"), field_two=(int, 123))
        >>> tuple_state = TupleStateModel()
        >>> assert tuple_state.field_one == "default"
        >>> assert tuple_state.field_two == 123

    Notes:
        - The function handles empty keyword arguments gracefully.
        - For tuple-based field definitions, the first element must be a valid Python type.
        - Unsupported value types in keyword arguments will raise a ValueError.
        - Callable methods must have proper return type annotations and belong to a class
          with a 'get_output_by_method' attribute when validate is True.
    """
    fields = {}
    computed_fields_dict = {}

    for name, value in kwargs.items():
        # Extract the return type from the method's type annotations
        if callable(value):
            # Define the field with the return type
            try:
                __validate_method(value)
                getter = build_output_getter(value, validate=validate)
                setter = build_output_setter(value, validate=validate)
                property_method = property(getter, setter)
            except ValueError as e:
                # If the method is not valid,assume it is already a getter
                if ("get_output_by_method" not in str(e) and "__self__" not in str(e)) or validate:
                    raise
                property_method = value
            # Store computed fields separately to add them to the base class
            computed_fields_dict[name] = computed_field(property_method)
        elif isinstance(value, FieldInfo):
            field_tuple = (value.annotation or Any, value)
            fields[name] = field_tuple
        elif isinstance(value, tuple) and len(value) == 2:  # noqa: PLR2004
            # Fields are defined by one of the following tuple forms:

            # (<type>, <default value>)
            # (<type>, Field(...))
            # typing.Annotated[<type>, Field(...)]
            if not isinstance(value[0], type):
                msg = f"Invalid type for field {name}: {type(value[0])}"
                raise TypeError(msg)
            fields[name] = (value[0], value[1])
        else:
            msg = f"Invalid value type {type(value)} for field {name}"
            raise ValueError(msg)

    # Create the model dynamically
    config_dict = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    # If we have computed fields, create a base class with them first
    if computed_fields_dict:
        # Create a base class with computed fields
        base_class_attrs = computed_fields_dict.copy()
        base_class_attrs["model_config"] = config_dict
        base_state_model = type(f"{model_name}Base", (BaseModel,), base_class_attrs)

        # Then create the final model with the base class
        return create_model(model_name, __base__=base_state_model, __config__=config_dict, **fields)
    # No computed fields, just create the model directly
    return create_model(model_name, __config__=config_dict, **fields)