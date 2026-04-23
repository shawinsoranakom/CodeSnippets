def from_template(
        cls: type[Self],
        template: str
        | list[str | _TextTemplateParam | _ImageTemplateParam | dict[str, Any]],
        template_format: PromptTemplateFormat = "f-string",
        *,
        partial_variables: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Self:
        """Create a class from a string template.

        Args:
            template: a template.
            template_format: format of the template.

                Options are: `'f-string'`, `'mustache'`, `'jinja2'`.
            partial_variables: A dictionary of variables that can be used too partially.

            **kwargs: Keyword arguments to pass to the constructor.

        Returns:
            A new instance of this class.

        Raises:
            ValueError: If the template is not a string or list of strings.
        """
        if isinstance(template, str):
            prompt: StringPromptTemplate | list = PromptTemplate.from_template(
                template,
                template_format=template_format,
                partial_variables=partial_variables,
            )
            return cls(prompt=prompt, **kwargs)
        if isinstance(template, list):
            if (partial_variables is not None) and len(partial_variables) > 0:
                msg = "Partial variables are not supported for list of templates."
                raise ValueError(msg)
            prompt = []
            for tmpl in template:
                if isinstance(tmpl, str) or (
                    isinstance(tmpl, dict)
                    and "text" in tmpl
                    and set(tmpl.keys()) <= {"type", "text"}
                ):
                    if isinstance(tmpl, str):
                        text: str = tmpl
                    else:
                        text = cast("_TextTemplateParam", tmpl)["text"]  # type: ignore[assignment]
                    prompt.append(
                        PromptTemplate.from_template(
                            text, template_format=template_format
                        )
                    )
                elif (
                    isinstance(tmpl, dict)
                    and "image_url" in tmpl
                    and set(tmpl.keys())
                    <= {
                        "type",
                        "image_url",
                    }
                ):
                    img_template = cast("_ImageTemplateParam", tmpl)["image_url"]
                    input_variables = []
                    if isinstance(img_template, str):
                        variables = get_template_variables(
                            img_template, template_format
                        )
                        if variables:
                            if len(variables) > 1:
                                msg = (
                                    "Only one format variable allowed per image"
                                    f" template.\nGot: {variables}"
                                    f"\nFrom: {tmpl}"
                                )
                                raise ValueError(msg)
                            input_variables = [variables[0]]
                        img_template = {"url": img_template}
                        img_template_obj = ImagePromptTemplate(
                            input_variables=input_variables,
                            template=img_template,
                            template_format=template_format,
                        )
                    elif isinstance(img_template, dict):
                        img_template = dict(img_template)
                        for key in ["url", "path", "detail"]:
                            if key in img_template:
                                input_variables.extend(
                                    get_template_variables(
                                        img_template[key], template_format
                                    )
                                )
                        img_template_obj = ImagePromptTemplate(
                            input_variables=input_variables,
                            template=img_template,
                            template_format=template_format,
                        )
                    else:
                        msg = f"Invalid image template: {tmpl}"
                        raise ValueError(msg)
                    prompt.append(img_template_obj)
                elif isinstance(tmpl, dict):
                    if template_format == "jinja2":
                        msg = (
                            "jinja2 is unsafe and is not supported for templates "
                            "expressed as dicts. Please use 'f-string' or 'mustache' "
                            "format."
                        )
                        raise ValueError(msg)
                    data_template_obj = DictPromptTemplate(
                        template=cast("dict[str, Any]", tmpl),
                        template_format=template_format,
                    )
                    prompt.append(data_template_obj)
                else:
                    msg = f"Invalid template: {tmpl}"
                    raise ValueError(msg)
            return cls(prompt=prompt, **kwargs)
        msg = f"Invalid template: {template}"
        raise ValueError(msg)