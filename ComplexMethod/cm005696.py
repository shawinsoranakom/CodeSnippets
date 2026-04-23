def __getattr__(self, name: str) -> Any:
        if name in self._objects:
            return self._objects[name]
        if name in self._object_missing_backend:
            missing_backends = self._object_missing_backend[name]

            # Backward-compat fallback: before the image processor refactoring, the base
            # `<Model>ImageProcessor` name referred to the PIL/slow backend. After the refactoring
            # it refers to the TorchvisionBackend (which requires torchvision). So if torchvision
            # is not installed, transparently fall back to `<Model>ImageProcessorPil` and warn once.
            if "torchvision" in missing_backends and name.endswith("ImageProcessor"):
                pil_name = f"{name}Pil"
                if pil_name in self._class_to_module and pil_name not in self._object_missing_backend:
                    try:
                        pil_module = self._get_module(self._class_to_module[pil_name])
                        pil_value = getattr(pil_module, pil_name)
                        logger.warning_once(
                            f"`{name}` requires torchvision (not installed); falling back to `{pil_name}` "
                            f"for backward compatibility. Install torchvision to use the default backend, "
                            f"or import `{pil_name}` directly to silence this warning."
                        )
                        setattr(self, name, pil_value)
                        return pil_value
                    except Exception as e:
                        logger.debug(f"Could not load PIL fallback {pil_name}: {e}")

            class Placeholder(metaclass=DummyObject):
                _backends = missing_backends

                def __init__(self, *args, **kwargs):
                    requires_backends(self, missing_backends)

                def call(self, *args, **kwargs):
                    pass

            Placeholder.__name__ = name

            if name not in self._class_to_module:
                module_name = f"transformers.{name}"
            else:
                module_name = self._class_to_module[name]
                if not module_name.startswith("transformers."):
                    module_name = f"transformers.{module_name}"

            Placeholder.__module__ = module_name

            value = Placeholder
        elif name in self._class_to_module:
            try:
                module = self._get_module(self._class_to_module[name])
                value = getattr(module, name)
            except (ModuleNotFoundError, RuntimeError, AttributeError) as e:
                # V5: If trying to import a *TokenizerFast symbol, transparently fall back to the
                # non-Fast symbol from the same module when available. This lets us keep only one
                # backend tokenizer class while preserving legacy public names.
                if name.endswith("TokenizerFast"):
                    fallback_name = name[:-4]
                    # Prefer importing the module that declares the fallback symbol if known
                    try:
                        if fallback_name in self._class_to_module:
                            fb_module = self._get_module(self._class_to_module[fallback_name])
                            fallback_value = getattr(fb_module, fallback_name)
                        else:
                            module = self._get_module(self._class_to_module[name])
                            fallback_value = getattr(module, fallback_name)
                        setattr(self, fallback_name, fallback_value)
                        value = fallback_value
                    except Exception:
                        # If we can't find the fallback here, try converter logic as a last resort
                        # before giving up
                        value = None
                        # Try converter mapping for Fast tokenizers that don't exist
                        if value is None and name.endswith("TokenizerFast"):
                            lookup_name = name[:-4]
                            try:
                                from ..convert_slow_tokenizer import SLOW_TO_FAST_CONVERTERS

                                if lookup_name in SLOW_TO_FAST_CONVERTERS:
                                    converter_class = SLOW_TO_FAST_CONVERTERS[lookup_name]
                                    converter_base_name = converter_class.__name__.replace("Converter", "")
                                    preferred_tokenizer_name = f"{converter_base_name}Tokenizer"

                                    candidate_names = [preferred_tokenizer_name]
                                    for tokenizer_name, tokenizer_converter in SLOW_TO_FAST_CONVERTERS.items():
                                        if tokenizer_converter is converter_class and tokenizer_name != lookup_name:
                                            if tokenizer_name not in candidate_names:
                                                candidate_names.append(tokenizer_name)

                                    # Try to import the preferred candidate directly
                                    import importlib

                                    for candidate_name in candidate_names:
                                        base_tokenizer_class = None

                                        # Try to derive module path from tokenizer name (e.g., "AlbertTokenizer" -> "albert")
                                        # Remove "Tokenizer" suffix and convert to lowercase
                                        if candidate_name.endswith("Tokenizer"):
                                            model_name = candidate_name[:-10].lower()  # Remove "Tokenizer"
                                            module_path = f"transformers.models.{model_name}.tokenization_{model_name}"
                                            try:
                                                module = importlib.import_module(module_path)
                                                base_tokenizer_class = getattr(module, candidate_name)
                                            except Exception:
                                                logger.debug(f"{module_path} does not have {candidate_name} defined.")

                                        # Fallback: try via _class_to_module
                                        if base_tokenizer_class is None and candidate_name in self._class_to_module:
                                            try:
                                                alias_module_name = self._class_to_module[candidate_name]
                                                alias_module = self._get_module(alias_module_name)
                                                base_tokenizer_class = getattr(alias_module, candidate_name)
                                            except Exception:
                                                logger.debug(
                                                    f"{alias_module_name} does not have {candidate_name} defined"
                                                )

                                        # If we still don't have base_tokenizer_class, skip this candidate
                                        if base_tokenizer_class is None:
                                            logger.debug(f"skipping candidate {candidate_name}")
                                            continue

                                        # If we got here, we have base_tokenizer_class
                                        value = base_tokenizer_class

                                        setattr(self, candidate_name, base_tokenizer_class)
                                        if lookup_name != candidate_name:
                                            setattr(self, lookup_name, value)
                                        setattr(self, name, value)
                                        break
                            except Exception as e:
                                logger.debug(f"Could not create tokenizer alias: {e}")

                        if value is None:
                            raise ModuleNotFoundError(
                                f"Could not import module '{name}'. Are this object's requirements defined correctly?"
                            ) from e
                else:
                    raise ModuleNotFoundError(
                        f"Could not import module '{name}'. Are this object's requirements defined correctly?"
                    ) from e

        elif name in self._modules:
            try:
                value = self._get_module(name)
            except (ModuleNotFoundError, RuntimeError) as e:
                raise ModuleNotFoundError(
                    f"Could not import module '{name}'. Are this object's requirements defined correctly?"
                ) from e
        else:
            # V5: If a *TokenizerFast symbol is requested but not present in the import structure,
            # try to resolve to the corresponding non-Fast symbol's module if available.
            if name.endswith("TokenizerFast"):
                fallback_name = name[:-4]
                if fallback_name in self._class_to_module:
                    try:
                        fb_module = self._get_module(self._class_to_module[fallback_name])
                        value = getattr(fb_module, fallback_name)
                        setattr(self, fallback_name, value)
                        setattr(self, name, value)
                        return value
                    except Exception as e:
                        logger.debug(f"Could not load fallback {fallback_name}: {e}")
            # V5: Handle *ImageProcessorFast backward compatibility
            # Similar to TokenizerFast, but for image processors
            if name.endswith("ImageProcessorFast"):
                fallback_name = name[:-4]  # Remove "Fast"
                if fallback_name in self._class_to_module:
                    logger.warning_once(
                        f"`{name}` is deprecated. The `Fast` suffix for image processors has been removed; "
                        f"use `{fallback_name}` instead."
                    )
                    if fallback_name in self._object_missing_backend:
                        # The Fast alias has no entry in the import structure, so `requires_backends` on
                        # the real class never runs. Handle the missing backend explicitly here, otherwise
                        # `_get_module` swallows the ImportError and the caller gets an AttributeError.
                        # Do not fall through to the PIL fallback since a legacy "Fast" image processor was explicitly requested.
                        missing_backends = self._object_missing_backend[fallback_name]

                        class Placeholder(metaclass=DummyObject):
                            _backends = missing_backends

                            def __init__(self, *args, **kwargs):
                                requires_backends(self, missing_backends)

                            def call(self, *args, **kwargs):
                                pass

                        Placeholder.__name__ = fallback_name
                        module_name = self._class_to_module[fallback_name]
                        Placeholder.__module__ = (
                            module_name if module_name.startswith("transformers.") else f"transformers.{module_name}"
                        )
                        setattr(self, name, Placeholder)
                        return Placeholder
                    try:
                        fb_module = self._get_module(self._class_to_module[fallback_name])
                        value = getattr(fb_module, fallback_name)
                        setattr(self, fallback_name, value)
                        setattr(self, name, value)
                        return value
                    except Exception as e:
                        logger.debug(f"Could not load fallback {fallback_name}: {e}")
            # V5: If a tokenizer class doesn't exist, check if it should alias to another tokenizer
            # via the converter mapping (e.g., FNetTokenizer -> AlbertTokenizer via AlbertConverter)
            value = None
            if name.endswith("Tokenizer") or name.endswith("TokenizerFast"):
                # Strip "Fast" suffix for converter lookup if present
                lookup_name = name[:-4] if name.endswith("TokenizerFast") else name

                try:
                    # Lazy import to avoid circular dependencies
                    from ..convert_slow_tokenizer import SLOW_TO_FAST_CONVERTERS

                    # Check if this tokenizer has a converter mapping
                    if lookup_name in SLOW_TO_FAST_CONVERTERS:
                        converter_class = SLOW_TO_FAST_CONVERTERS[lookup_name]

                        # Find which tokenizer class uses the same converter (reverse lookup)
                        # Prefer the tokenizer that matches the converter name pattern
                        # (e.g., AlbertConverter -> AlbertTokenizer)
                        converter_base_name = converter_class.__name__.replace("Converter", "")
                        preferred_tokenizer_name = f"{converter_base_name}Tokenizer"

                        # Try preferred tokenizer first
                        candidate_names = [preferred_tokenizer_name]
                        # Then try all other tokenizers with the same converter
                        for tokenizer_name, tokenizer_converter in SLOW_TO_FAST_CONVERTERS.items():
                            if tokenizer_converter is converter_class and tokenizer_name != lookup_name:
                                if tokenizer_name not in candidate_names:
                                    candidate_names.append(tokenizer_name)

                        # Try to import one of the candidate tokenizers
                        for candidate_name in candidate_names:
                            if candidate_name in self._class_to_module:
                                try:
                                    alias_module = self._get_module(self._class_to_module[candidate_name])
                                    base_tokenizer_class = getattr(alias_module, candidate_name)
                                    value = base_tokenizer_class

                                    # Cache both names for future imports
                                    setattr(self, candidate_name, base_tokenizer_class)
                                    if lookup_name != candidate_name:
                                        setattr(self, lookup_name, value)
                                    setattr(self, name, value)
                                    break
                                except Exception:
                                    # If this candidate fails, try the next one
                                    continue
                            else:
                                # Candidate not in _class_to_module - might need recursive resolution
                                # Try importing it directly to trigger lazy loading
                                try:
                                    # Try to get it from transformers module to trigger lazy loading
                                    transformers_module = sys.modules.get("transformers")
                                    if transformers_module and hasattr(transformers_module, candidate_name):
                                        base_tokenizer_class = getattr(transformers_module, candidate_name)
                                        value = base_tokenizer_class

                                        if lookup_name != candidate_name:
                                            setattr(self, lookup_name, value)
                                        setattr(self, name, value)
                                        break
                                except Exception:
                                    continue
                except (ImportError, AttributeError):
                    pass

            if value is None:
                for key, values in self._explicit_import_shortcut.items():
                    if name in values:
                        value = self._get_module(key)
                        break

            if value is None:
                raise AttributeError(f"module {self.__name__} has no attribute {name}")

        setattr(self, name, value)
        return value