def validate_instantiation(component: ComponentModel) -> Optional[ValidationError]:
        """Validate that the component can be instantiated"""
        try:
            model = component.model_copy(deep=True)

            # SECURITY: Skip instantiation for FunctionTool to prevent arbitrary code execution.
            # FunctionTool._from_config() uses exec() on user-provided source_code, which is an RCE vector.
            # Schema validation is sufficient for FunctionTool - we validate the config structure without
            # actually executing the code. This blocks drive-by attacks via the /api/validate/ endpoint.
            if "FunctionTool" in model.provider:
                return None

            # Attempt to load the component
            module_path, class_name = model.provider.rsplit(".", maxsplit=1)
            module = importlib.import_module(module_path)
            component_class = getattr(module, class_name)
            component_class.load_component(model)
            return None
        except Exception as e:
            error_str = str(e)

            # Check for version compatibility issues
            if "component_version" in error_str and "_from_config_past_version is not implemented" in error_str:
                # Extract component information for a better error message
                try:
                    # Get the current component version
                    module_path, class_name = component.provider.rsplit(".", maxsplit=1)
                    module = importlib.import_module(module_path)
                    component_class = getattr(module, class_name)
                    current_version = getattr(component_class, "component_version", None)
                    config_version = component.component_version or component.version or 1

                    return ValidationError(
                        field="component_version",
                        error=f"Component version mismatch: Your configuration uses version {config_version}, but the component requires version {current_version}",
                        suggestion=f"Update your component configuration to use version {current_version}. Set 'component_version: {current_version}' in your configuration.",
                    )
                except Exception:
                    # Fallback to a more general version error message
                    return ValidationError(
                        field="component_version",
                        error="Component version compatibility issue detected",
                        suggestion="Your component configuration version is outdated. Update the 'component_version' field to match the latest component requirements.",
                    )

            # Check for other common instantiation issues
            elif "Could not import provider" in error_str or "ImportError" in error_str:
                return ValidationError(
                    field="provider",
                    error=f"Provider import failed: {error_str}",
                    suggestion="Ensure the provider module is installed and the import path is correct",
                )
            elif "component_config_schema" in error_str:
                return ValidationError(
                    field="config",
                    error="Component configuration schema validation failed",
                    suggestion="Check that your configuration matches the component's expected schema",
                )
            else:
                return ValidationError(
                    field="instantiation",
                    error=f"Failed to instantiate component: {error_str}",
                    suggestion="Check that the component can be properly instantiated with the given config",
                )