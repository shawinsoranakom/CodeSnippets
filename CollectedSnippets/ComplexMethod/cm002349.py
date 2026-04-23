def infer_new_model_name(self) -> dict:
        """Infer whether we are using a model name prefix different from the usual model name as defined from the filename.
        This is useful e.g. when we define a new multi-modal model, and only the text part inherits from `LlamaModel`,
        so we have something like:
        ```python
        class NewModelNameTextDecoderLayer(LlamaDecoderLayer):
            pass
        ```
        with the `Text` prefix added to the model name.
        However, in case of multiple prefix used, we raise a warning and use the most frequent prefix, to avoid parsing
        the same file multiple times and inconsistencies in the objects added from dependencies.
        If the new prefix collides with a prefix of another class in the file where we are importing from, then we also
        raise a warning, and use the default prefix (model name) to avoid collisions in dependencies.
        """
        prefix_model_name_mapping = defaultdict(Counter)
        cased_default_name = get_cased_name(self.model_name)
        # Iterate over all new classes to get modeling super classes
        for class_name, class_node in self.classes.items():
            modeling_bases = [
                k.value.value for k in class_node.bases if k.value.value in self.model_specific_imported_objects
            ]
            if len(modeling_bases) > 1:
                raise ValueError(
                    f"{class_name} was defined with more than 1 model-specific super class. This is unsupported. We found {(*modeling_bases,)}."
                )
            if len(modeling_bases) == 1:
                filename = self.model_specific_imported_objects[modeling_bases[0]]
                cased_model_name = cased_default_name  # the default name prefix
                suffix = common_partial_suffix(class_name, modeling_bases[0])
                if len(suffix) > 0 and suffix[0].isupper():
                    cased_model_name = class_name.replace(suffix, "")
                    # If both the old model and new model share the last part of their name, it is detected as a common
                    # suffix, but it should not be the case -> use the full name in this case
                    if len(cased_model_name) < len(cased_default_name) and cased_default_name in class_name:
                        cased_model_name = cased_default_name
                # If the new class name is of the form ` class NewNameOldNameClass(OldNameClass):`, i.e. it contains both names,
                # add the OldName as suffix (see `examples/modular-transformers/modular_test_suffix.py`)
                elif class_name.replace(cased_default_name, "") == modeling_bases[0]:
                    file_model_name = filename.split(".")[-2]
                    cased_model_name = cased_default_name + get_cased_name(file_model_name)
                prefix_model_name_mapping[filename].update([cased_model_name])

        # Check if we found multiple prefixes for some modeling files
        final_name_mapping = {}
        for file, prefixes_counter in prefix_model_name_mapping.items():
            if len(prefixes_counter) > 1:
                _, total = prefixes_counter.most_common(1)[0]
                most_used_entities = [name for name, count in prefixes_counter.most_common() if count == total]
                # if the default name is in the pool of equally used prefixes, use it, otherwise last encountered
                final_name = cased_default_name if cased_default_name in most_used_entities else most_used_entities[-1]
            else:
                final_name = list(prefixes_counter)[0]
            # Check if the prefix can be used without collisions in the names
            old_cased_model_name = get_cased_name(file.split(".")[-2])
            old_model_name_prefix = final_name.replace(cased_default_name, old_cased_model_name)
            # Raise adequate warning depending on the situation
            has_prefix_collision = f"\nclass {old_model_name_prefix}" in get_module_source_from_name(file)
            if final_name != cased_default_name and has_prefix_collision:
                if len(prefixes_counter) > 1:
                    logger.warning(
                        f"We detected multiple prefix names when inheriting from {file}: {(*set(prefixes_counter),)}. However, the "
                        f"most used one, '{final_name}', is already present in the source file and will likely cause consistency "
                        f"issues. For this reason we fallback to the default prefix '{cased_default_name}' when grabbing args "
                        "and dependencies. Make sure to subclass the intermediate classes with the prefix you want (if different "
                        f"from '{cased_default_name}') or use a single prefix in all the modular (best)."
                    )
                else:
                    logger.warning(
                        f"We detected the use of the new default prefix {final_name} when inheriting from {file}. However, it is "
                        "already present in the source file and will likely cause consistency issues. For this reason we fallback "
                        f"to the default prefix '{cased_default_name}' when grabbing args and dependencies. Make sure to subclass "
                        f"the intermediate classes with the prefix you want (if different from '{cased_default_name}')"
                    )
                final_name = cased_default_name
            elif len(prefixes_counter) > 1:
                logger.warning(
                    f"We detected multiple prefix names when inheriting from {file}: {(*set(prefixes_counter),)}. We will only "
                    f"use the most used '{final_name}' prefix when grabbing args and dependencies. Make sure to subclass the "
                    f"intermediate classes with the prefix you want (if different from '{final_name}') or use a single prefix "
                    "in all the modular (best)."
                )
            final_name_mapping[file] = get_lowercase_name(final_name)

        # Check we are not missing imported files
        for file in self.model_specific_modules:
            if file not in final_name_mapping:
                final_name_mapping[file] = self.model_name

        return final_name_mapping