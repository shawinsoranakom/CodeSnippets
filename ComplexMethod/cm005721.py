def auto_class_docstring(cls, custom_intro=None, custom_args=None, checkpoint=None):
    """
    Wrapper that automatically generates a docstring for classes based on their attributes and methods.
    """
    # import here to avoid circular import
    from transformers.models import auto as auto_module

    is_dataclass = False
    is_processor = False
    is_config = False
    is_image_processor = False
    docstring_init = ""
    docstring_args = ""
    if "PreTrainedModel" in (x.__name__ for x in cls.__mro__):
        docstring_init = auto_method_docstring(
            cls.__init__, parent_class=cls, custom_args=custom_args, checkpoint=checkpoint
        ).__doc__.replace("Args:", "Parameters:")
    elif "ProcessorMixin" in (x.__name__ for x in cls.__mro__):
        is_processor = True
        docstring_init = auto_method_docstring(
            cls.__init__,
            parent_class=cls,
            custom_args=custom_args,
            checkpoint=checkpoint,
            source_args_dict=get_args_doc_from_source([ModelArgs, ImageProcessorArgs, ProcessorArgs]),
        ).__doc__.replace("Args:", "Parameters:")
    elif "ModelOutput" in (x.__name__ for x in cls.__mro__):
        # We have a data class
        is_dataclass = True
        doc_class = cls.__doc__
        if custom_args is None and doc_class:
            custom_args = doc_class
        docstring_args = auto_method_docstring(
            cls.__init__,
            parent_class=cls,
            custom_args=custom_args,
            checkpoint=checkpoint,
            source_args_dict=get_args_doc_from_source(ModelOutputArgs),
        ).__doc__
    elif any("BaseImageProcessor" in x.__name__ for x in cls.__mro__):
        is_image_processor = True
        docstring_init = auto_method_docstring(
            cls.__init__,
            parent_class=cls,
            custom_args=custom_args,
            checkpoint=checkpoint,
            source_args_dict=get_args_doc_from_source(ImageProcessorArgs),
        ).__doc__
    elif "PreTrainedConfig" in (x.__name__ for x in cls.__mro__):
        is_config = True
        doc_class = cls.__doc__
        if custom_args is None and doc_class:
            custom_args = doc_class

        # Collect all non-ClassVar annotations from the class and its ancestors up to
        # (but not including) PreTrainedConfig. This allows inherited params from intermediate
        # config base classes to be documented, while naturally excluding PreTrainedConfig-specific
        # quasi-ClassVar params (e.g. `transformers_version`, `architectures`).
        own_config_params = set()
        for ancestor in cls.__mro__:
            if ancestor.__name__ == "PreTrainedConfig":
                break
            own_config_params |= {
                k for k, v in getattr(ancestor, "__annotations__", {}).items() if get_origin(v) is not ClassVar
            }
        allowed_params = own_config_params if own_config_params else None
        docstring_init = auto_method_docstring(
            cls.__init__,
            parent_class=cls,
            custom_args=custom_args,
            checkpoint=checkpoint,
            source_args_dict=get_args_doc_from_source([ConfigArgs]),
            allowed_params=allowed_params,
        ).__doc__

    indent_level = get_indent_level(cls)
    model_name_lowercase = get_model_name(cls)
    model_name_title = " ".join([k.title() for k in model_name_lowercase.split("_")]) if model_name_lowercase else None
    model_base_class = f"{model_name_title.title()}Model" if model_name_title is not None else None
    if model_name_lowercase is not None:
        try:
            model_base_class = getattr(
                getattr(auto_module, PLACEHOLDER_TO_AUTO_MODULE["model_class"][0]),
                PLACEHOLDER_TO_AUTO_MODULE["model_class"][1],
            )[model_name_lowercase]
        except KeyError:
            pass
        except ImportError:
            # In some environments, certain model classes might not be available. In that case, we can skip this part.
            pass

    if model_name_lowercase and model_name_lowercase not in getattr(
        getattr(auto_module, PLACEHOLDER_TO_AUTO_MODULE["config_class"][0]),
        PLACEHOLDER_TO_AUTO_MODULE["config_class"][1],
    ):
        model_name_lowercase = model_name_lowercase.replace("_", "-")

    name = re.findall(rf"({'|'.join(ClassDocstring.__dict__.keys())})$", cls.__name__)

    if name == [] and custom_intro is None and not is_dataclass and not is_processor and not is_image_processor:
        raise ValueError(
            f"`{cls.__name__}` is not registered in the auto doc. Here are the available classes: {ClassDocstring.__dict__.keys()}.\n"
            "Add a `custom_intro` to the decorator if you want to use `auto_docstring` on a class not registered in the auto doc."
        )
    if name != [] or custom_intro is not None or is_config or is_dataclass or is_processor or is_image_processor:
        name = name[0] if name else None
        formatting_kwargs = {"model_name": model_name_title}
        if name == "Config":
            formatting_kwargs.update({"model_base_class": model_base_class, "model_checkpoint": checkpoint})
        if custom_intro is not None:
            pre_block = equalize_indent(custom_intro, indent_level)
            if not pre_block.endswith("\n"):
                pre_block += "\n"
        elif is_processor:
            # Generate processor intro dynamically
            pre_block = generate_processor_intro(cls)
            if pre_block:
                pre_block = equalize_indent(pre_block, indent_level)
                pre_block = format_args_docstring(pre_block, model_name_lowercase)
        elif is_image_processor:
            pre_block = r"Constructs a {image_processor_class} image processor."
            if pre_block:
                pre_block = equalize_indent(pre_block, indent_level)
                pre_block = format_args_docstring(pre_block, model_name_lowercase)
        elif model_name_title is None or name is None:
            pre_block = ""
        else:
            pre_block = getattr(ClassDocstring, name).format(**formatting_kwargs)
        # Start building the docstring
        docstring = set_min_indent(f"{pre_block}", indent_level) if len(pre_block) else ""
        if name != "PreTrainedModel" and "PreTrainedModel" in (x.__name__ for x in cls.__mro__):
            docstring += set_min_indent(f"{ClassDocstring.PreTrainedModel}", indent_level)
        # Add the __init__ docstring
        if docstring_init:
            docstring += set_min_indent(f"\n{docstring_init}", indent_level)
        elif is_dataclass or is_config:
            # No init function, we have a data class
            docstring += docstring_args if docstring_args else "\nArgs:\n"
            source_args_dict = get_args_doc_from_source(ModelOutputArgs)
            doc_class = cls.__doc__ if cls.__doc__ else ""
            documented_kwargs = parse_docstring(doc_class)[0]
            for param_name, param_type_annotation in cls.__annotations__.items():
                param_type, optional = process_type_annotation(param_type_annotation, param_name)

                # Check for default value
                param_default = ""
                param_default = str(getattr(cls, param_name, ""))
                param_default = f", defaults to `{param_default}`" if param_default != "" else ""

                param_type, optional_string, shape_string, additional_info, description, is_documented = (
                    _get_parameter_info(param_name, documented_kwargs, source_args_dict, param_type, optional)
                )

                if is_documented:
                    # Check if type is missing
                    if param_type == "":
                        print(
                            f"[ERROR] {param_name} for {cls.__qualname__} in file {cls.__code__.co_filename} has no type"
                        )
                    param_type = param_type if "`" in param_type else f"`{param_type}`"
                    # Format the parameter docstring
                    if additional_info:
                        docstring += set_min_indent(
                            f"{param_name} ({param_type}{additional_info}):{description}",
                            indent_level + 8,
                        )
                    else:
                        docstring += set_min_indent(
                            f"{param_name} ({param_type}{shape_string}{optional_string}{param_default}):{description}",
                            indent_level + 8,
                        )
        # TODO (Yoni): Add support for Attributes section in docs

    else:
        print(
            f"You used `@auto_class_docstring` decorator on `{cls.__name__}` but this class is not part of the AutoMappings. Remove the decorator"
        )
    # Assign the dynamically generated docstring to the wrapper class
    cls.__doc__ = docstring

    return cls