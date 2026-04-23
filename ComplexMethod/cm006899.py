async def load_custom_component(component_name: str, components_paths: list[str]):
    """Load a custom component by name.

    Args:
        component_name: Name of the component to load
        components_paths: List of paths to search for components
    """
    from lfx.interface.custom_component import get_custom_component_from_name

    try:
        # First try to get the component from the registered components
        component_class = get_custom_component_from_name(component_name)
        if component_class:
            # Define the function locally if it's not imported
            def get_custom_component_template(component_cls):
                """Get template for a custom component class."""
                # This is a simplified implementation - adjust as needed
                if hasattr(component_cls, "get_template"):
                    return component_cls.get_template()
                if hasattr(component_cls, "template"):
                    return component_cls.template
                return None

            return get_custom_component_template(component_class)

        # If not found in registered components, search in the provided paths
        for path in components_paths:
            # Try to find the component in different category directories
            base_path = Path(path)
            if base_path.exists() and base_path.is_dir():
                # Search for the component in all subdirectories
                for category_dir in base_path.iterdir():
                    if category_dir.is_dir():
                        component_file = category_dir / f"{component_name}.py"
                        if component_file.exists():
                            # Try to import the module
                            module_name = f"lfx.components.{category_dir.name}.{component_name}"
                            try:
                                import importlib.util

                                spec = importlib.util.spec_from_file_location(module_name, component_file)
                                if spec and spec.loader:
                                    module = importlib.util.module_from_spec(spec)
                                    spec.loader.exec_module(module)
                                    if hasattr(module, "template"):
                                        return module.template
                                    if hasattr(module, "get_template"):
                                        return module.get_template()
                            except ImportError as e:
                                await logger.aerror(f"Import error loading component {component_file}: {e!s}")
                                await logger.adebug("Import error traceback", exc_info=True)
                            except AttributeError as e:
                                await logger.aerror(f"Attribute error loading component {component_file}: {e!s}")
                                await logger.adebug("Attribute error traceback", exc_info=True)
                            except (ValueError, TypeError) as e:
                                await logger.aerror(f"Value/Type error loading component {component_file}: {e!s}")
                                await logger.adebug("Value/Type error traceback", exc_info=True)
                            except (KeyError, IndexError) as e:
                                await logger.aerror(f"Data structure error loading component {component_file}: {e!s}")
                                await logger.adebug("Data structure error traceback", exc_info=True)
                            except RuntimeError as e:
                                await logger.aerror(f"Runtime error loading component {component_file}: {e!s}")
                                await logger.adebug("Runtime error traceback", exc_info=True)
                            except OSError as e:
                                await logger.aerror(f"OS error loading component {component_file}: {e!s}")
                                await logger.adebug("OS error traceback", exc_info=True)

    except ImportError as e:
        await logger.aerror(f"Import error loading custom component {component_name}: {e!s}")
        return None
    except AttributeError as e:
        await logger.aerror(f"Attribute error loading custom component {component_name}: {e!s}")
        return None
    except ValueError as e:
        await logger.aerror(f"Value error loading custom component {component_name}: {e!s}")
        return None
    except (KeyError, IndexError) as e:
        await logger.aerror(f"Data structure error loading custom component {component_name}: {e!s}")
        return None
    except RuntimeError as e:
        await logger.aerror(f"Runtime error loading custom component {component_name}: {e!s}")
        logger.debug("Full traceback for runtime error", exc_info=True)
        return None

    # If we get here, the component wasn't found in any of the paths
    await logger.awarning(f"Component {component_name} not found in any of the provided paths")
    return None