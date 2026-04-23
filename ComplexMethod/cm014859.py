def check_one_element(elem, modname, mod, *, is_public, is_all):
                obj = getattr(mod, elem)

                # torch.dtype is not a class nor callable, so we need to check for it separately
                if not (
                    isinstance(obj, (Callable, torch.dtype)) or inspect.isclass(obj)
                ):
                    return
                elem_module = getattr(obj, "__module__", None)

                # Only used for nice error message below
                why_not_looks_public = ""
                if elem_module is None:
                    why_not_looks_public = (
                        "because it does not have a `__module__` attribute"
                    )

                # If a module is being migrated from foo.a to bar.a (that is entry {"foo": "bar"}),
                # the module's starting package would be referred to as the new location even
                # if there is a "from foo import a" inside the "bar.py".
                modname = allow_dict["being_migrated"].get(modname, modname)
                elem_modname_starts_with_mod = (
                    elem_module is not None
                    and elem_module.startswith(modname)
                    and "._" not in elem_module
                )
                if not why_not_looks_public and not elem_modname_starts_with_mod:
                    why_not_looks_public = (
                        f"because its `__module__` attribute (`{elem_module}`) is not within the "
                        f"torch library or does not start with the submodule where it is defined (`{modname}`)"
                    )

                # elem's name must NOT begin with an `_` and it's module name
                # SHOULD start with it's current module since it's a public API
                looks_public = not elem.startswith("_") and elem_modname_starts_with_mod
                if not why_not_looks_public and not looks_public:
                    why_not_looks_public = f"because it starts with `_` (`{elem}`)"
                if is_public != looks_public:
                    if modname in allow_dict and elem in allow_dict[modname]:
                        return
                    if is_public:
                        why_is_public = (
                            f"it is inside the module's (`{modname}`) `__all__`"
                            if is_all
                            else "it is an attribute that does not start with `_` on a module that "
                            "does not have `__all__` defined"
                        )
                        fix_is_public = (
                            f"remove it from the modules' (`{modname}`) `__all__`"
                            if is_all
                            else f"either define a `__all__` for `{modname}` or add a `_` at the beginning of the name"
                        )
                    else:
                        if not is_all:
                            raise AssertionError(
                                f"Expected {modname}.{elem} to be checked via __all__"
                            )
                        why_is_public = (
                            f"it is not inside the module's (`{modname}`) `__all__`"
                        )
                        fix_is_public = (
                            f"add it from the modules' (`{modname}`) `__all__`"
                        )
                    if looks_public:
                        why_looks_public = (
                            "it does look public because it follows the rules from the doc above "
                            "(does not start with `_` and has a proper `__module__`)."
                        )
                        fix_looks_public = "make its name start with `_`"
                    else:
                        why_looks_public = why_not_looks_public
                        if not elem_modname_starts_with_mod:
                            fix_looks_public = (
                                "make sure the `__module__` is properly set and points to a submodule "
                                f"of `{modname}`"
                            )
                        else:
                            fix_looks_public = (
                                "remove the `_` at the beginning of the name"
                            )
                    failure_list.append(f"# {modname}.{elem}:")
                    is_public_str = "" if is_public else " NOT"
                    failure_list.append(
                        f"  - Is{is_public_str} public: {why_is_public}"
                    )
                    looks_public_str = "" if looks_public else " NOT"
                    failure_list.append(
                        f"  - Does{looks_public_str} look public: {why_looks_public}"
                    )
                    # Swap the str below to avoid having to create the NOT again
                    failure_list.append(
                        "  - You can do either of these two things to fix this problem:"
                    )
                    failure_list.append(
                        f"    - To make it{looks_public_str} public: {fix_is_public}"
                    )
                    failure_list.append(
                        f"    - To make it{is_public_str} look public: {fix_looks_public}"
                    )