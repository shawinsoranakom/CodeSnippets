async def get_single_component_dict(component_type: str, component_name: str, components_paths: list[str]):
    """Get a single component dictionary."""
    # For example, if components are loaded by importing Python modules:
    for base_path in components_paths:
        module_path = Path(base_path) / component_type / f"{component_name}.py"
        if module_path.exists():
            # Try to import the module
            module_name = f"lfx.components.{component_type}.{component_name}"
            try:
                # This is a simplified example - actual implementation may vary
                import importlib.util

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "template"):
                        return module.template
            except ImportError as e:
                await logger.aerror(f"Import error loading component {module_path}: {e!s}")
            except AttributeError as e:
                await logger.aerror(f"Attribute error loading component {module_path}: {e!s}")
            except ValueError as e:
                await logger.aerror(f"Value error loading component {module_path}: {e!s}")
            except (KeyError, IndexError) as e:
                await logger.aerror(f"Data structure error loading component {module_path}: {e!s}")
            except RuntimeError as e:
                await logger.aerror(f"Runtime error loading component {module_path}: {e!s}")
                await logger.adebug("Full traceback for runtime error", exc_info=True)
            except OSError as e:
                await logger.aerror(f"OS error loading component {module_path}: {e!s}")

    # If we get here, the component wasn't found or couldn't be loaded
    return None