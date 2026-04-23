def check_file(filename: str) -> list[LintMessage]:
    path = Path(filename).absolute()
    try:
        pyproject = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as err:
        return [format_error_message(filename, err)]

    if not (isinstance(pyproject, dict) and isinstance(pyproject.get("project"), dict)):
        return [
            format_error_message(
                filename,
                message=(
                    "'project' section in pyproject.toml must present and be a table."
                ),
            )
        ]

    project = pyproject["project"]
    requires_python = project.get("requires-python")
    if requires_python is not None:
        if not isinstance(requires_python, str):
            return [
                format_error_message(
                    filename,
                    message="'project.requires-python' must be a string.",
                )
            ]

        python_major = 3
        specifier_set = SpecifierSet(requires_python)
        for specifier in specifier_set:
            if Version(specifier.version).major != python_major:
                return [
                    format_error_message(
                        filename,
                        message=(
                            "'project.requires-python' must only specify "
                            f"Python {python_major} versions, but found {specifier.version}."
                        ),
                    )
                ]

        large_minor = 1000
        supported_python_versions = list(
            specifier_set.filter(
                f"{python_major}.{minor}" for minor in range(large_minor + 1)
            )
        )
        if not supported_python_versions:
            return [
                format_error_message(
                    filename,
                    message=(
                        "'project.requires-python' must specify at least one "
                        f"Python {python_major} version, but found {requires_python!r}."
                    ),
                )
            ]
        if f"{python_major}.0" in supported_python_versions:
            return [
                format_error_message(
                    filename,
                    message=(
                        "'project.requires-python' must specify a minimum version, "
                        f"but found {requires_python!r}."
                    ),
                )
            ]
        # if f"{python_major}.{large_minor}" in supported_python_versions:
        #     return [
        #         format_error_message(
        #             filename,
        #             message=(
        #                 "'project.requires-python' must specify a maximum version, "
        #                 f"but found {requires_python!r}."
        #             ),
        #         )
        #     ]

        classifiers = project.get("classifiers")
        if not (
            isinstance(classifiers, list)
            and all(isinstance(c, str) for c in classifiers)
        ):
            return [
                format_error_message(
                    filename,
                    message="'project.classifiers' must be an array of strings.",
                )
            ]
        if len(set(classifiers)) != len(classifiers):
            return [
                format_error_message(
                    filename,
                    message="'project.classifiers' must not contain duplicates.",
                )
            ]

        # python_version_classifiers = [
        #     c
        #     for c in classifiers
        #     if (
        #         c.startswith("Programming Language :: Python :: ")
        #         and not c.endswith((f":: {python_major}", f":: {python_major} :: Only"))
        #     )
        # ]
        # if python_version_classifiers:
        #     python_version_classifier_set = set(python_version_classifiers)
        #     supported_python_version_classifier_set = {
        #         f"Programming Language :: Python :: {v}"
        #         for v in supported_python_versions
        #     }
        #     if python_version_classifier_set != supported_python_version_classifier_set:
        #         missing_classifiers = sorted(
        #             supported_python_version_classifier_set
        #             - python_version_classifier_set
        #         )
        #         extra_classifiers = sorted(
        #             python_version_classifier_set
        #             - supported_python_version_classifier_set
        #         )
        #         if missing_classifiers:
        #             return [
        #                 format_error_message(
        #                     filename,
        #                     message=(
        #                         "'project.classifiers' is missing the following classifier(s):\n"
        #                         + "\n".join(f"  {c!r}" for c in missing_classifiers)
        #                     ),
        #                 )
        #             ]
        #         if extra_classifiers:
        #             return [
        #                 format_error_message(
        #                     filename,
        #                     message=(
        #                         "'project.classifiers' contains extra classifier(s):\n"
        #                         + "\n".join(f"  {c!r}" for c in extra_classifiers)
        #                     ),
        #                 )
        #             ]

    return []