def generate_stub_file(cls, async_class: type, sync_class: type) -> None:
        """
        Generate a .pyi stub file for the sync class to help IDEs with type checking.
        """
        try:
            # Only generate stub if we can determine module path
            if async_class.__module__ == "__main__":
                return

            module = inspect.getmodule(async_class)
            if not module:
                return

            module_path = module.__file__
            if not module_path:
                return

            # Create stub file path in a 'generated' subdirectory
            module_dir = os.path.dirname(module_path)
            stub_dir = os.path.join(module_dir, "generated")

            # Ensure the generated directory exists
            os.makedirs(stub_dir, exist_ok=True)

            module_name = os.path.basename(module_path)
            if module_name.endswith(".py"):
                module_name = module_name[:-3]

            sync_stub_path = os.path.join(stub_dir, f"{sync_class.__name__}.pyi")

            # Create a type tracker for this stub generation
            type_tracker = TypeTracker()

            stub_content = []

            # We'll generate imports after processing all methods to capture all types
            # Leave a placeholder for imports
            imports_placeholder_index = len(stub_content)
            stub_content.append("")  # Will be replaced with imports later

            # Class definition
            stub_content.append(f"class {sync_class.__name__}:")

            # Docstring
            if async_class.__doc__:
                stub_content.extend(
                    cls._format_docstring_for_stub(async_class.__doc__, "    ")
                )

            # Generate __init__
            try:
                init_method = async_class.__init__
                init_signature = inspect.signature(init_method)

                # Try to get type hints for __init__
                try:
                    from typing import get_type_hints
                    init_hints = get_type_hints(init_method)
                except Exception:
                    init_hints = {}

                # Format parameters
                params_str = cls._format_method_parameters(
                    init_signature, type_hints=init_hints, type_tracker=type_tracker
                )
                # Add __init__ docstring if available (before the method)
                if hasattr(init_method, "__doc__") and init_method.__doc__:
                    stub_content.extend(
                        cls._format_docstring_for_stub(init_method.__doc__, "    ")
                    )
                stub_content.append(f"    def __init__({params_str}) -> None: ...")
            except (ValueError, TypeError):
                stub_content.append(
                    "    def __init__(self, *args, **kwargs) -> None: ..."
                )

            stub_content.append("")  # Add newline after __init__

            # Get class attributes
            class_attributes = cls._get_class_attributes(async_class)

            # Generate inner classes
            for name, attr in class_attributes:
                inner_class_stub = cls._generate_inner_class_stub(
                    name, attr, type_tracker=type_tracker
                )
                stub_content.extend(inner_class_stub)
                stub_content.append("")  # Add newline after the inner class

            # Add methods to the main class
            processed_methods = set()  # Keep track of methods we've processed
            for name, method in sorted(
                inspect.getmembers(async_class, predicate=inspect.isfunction)
            ):
                if name.startswith("_") or name in processed_methods:
                    continue

                processed_methods.add(name)

                try:
                    method_sig = cls._generate_method_signature(
                        name, method, is_async=True, type_tracker=type_tracker
                    )

                    # Add docstring if available (before the method signature for proper formatting)
                    if method.__doc__:
                        stub_content.extend(
                            cls._format_docstring_for_stub(method.__doc__, "    ")
                        )

                    stub_content.append(f"    {method_sig}")

                    stub_content.append("")  # Add newline after each method

                except (ValueError, TypeError):
                    # If we can't get the signature, just add a simple stub
                    stub_content.append(f"    def {name}(self, *args, **kwargs): ...")
                    stub_content.append("")  # Add newline

            # Add properties
            for name, prop in sorted(
                inspect.getmembers(async_class, lambda x: isinstance(x, property))
            ):
                stub_content.append("    @property")
                stub_content.append(f"    def {name}(self) -> Any: ...")
                if prop.fset:
                    stub_content.append(f"    @{name}.setter")
                    stub_content.append(
                        f"    def {name}(self, value: Any) -> None: ..."
                    )
                stub_content.append("")  # Add newline after each property

            # Add placeholders for the nested class instances
            # Check the actual attribute names from class annotations and attributes
            attribute_mappings = {}

            # First check annotations for typed attributes (including from parent classes)
            # Resolve string annotations to actual types
            try:
                all_annotations = get_type_hints(async_class)
            except Exception:
                # Fallback to raw annotations
                all_annotations = {}
                for base_class in reversed(inspect.getmro(async_class)):
                    if hasattr(base_class, "__annotations__"):
                        all_annotations.update(base_class.__annotations__)

            for attr_name, attr_type in sorted(all_annotations.items()):
                for class_name, class_type in class_attributes:
                    # If the class type matches the annotated type
                    if (
                        attr_type == class_type
                        or (hasattr(attr_type, "__name__") and attr_type.__name__ == class_name)
                        or (isinstance(attr_type, str) and attr_type == class_name)
                    ):
                        attribute_mappings[class_name] = attr_name

            # Remove the extra checking - annotations should be sufficient

            # Add the attribute declarations with proper names
            for class_name, class_type in class_attributes:
                # Check if there's a mapping from annotation
                attr_name = attribute_mappings.get(class_name, class_name)
                # Use the annotation name if it exists, even if the attribute doesn't exist yet
                # This is because the attribute might be created at runtime
                stub_content.append(f"    {attr_name}: {class_name}Sync")

            stub_content.append("")  # Add a final newline

            # Now generate imports with all discovered types
            imports = cls._generate_imports(async_class, type_tracker)

            # Deduplicate imports while preserving order
            seen = set()
            unique_imports = []
            for imp in imports:
                if imp not in seen:
                    seen.add(imp)
                    unique_imports.append(imp)
                else:
                    logging.warning(f"Duplicate import detected: {imp}")

            # Replace the placeholder with actual imports
            stub_content[imports_placeholder_index : imports_placeholder_index + 1] = (
                unique_imports
            )

            # Post-process stub content
            stub_content = cls._post_process_stub_content(stub_content)

            # Write stub file
            with open(sync_stub_path, "w") as f:
                f.write("\n".join(stub_content))

            logging.info(f"Generated stub file: {sync_stub_path}")

        except Exception as e:
            # If stub generation fails, log the error but don't break the main functionality
            logging.error(
                f"Error generating stub file for {sync_class.__name__}: {str(e)}"
            )
            import traceback

            logging.error(traceback.format_exc())