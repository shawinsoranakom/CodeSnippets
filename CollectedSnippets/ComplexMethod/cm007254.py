async def load_single_component(component_type: str, component_name: str, components_paths: list[str]):
    """Load a single component fully."""
    from lfx.custom.utils import get_single_component_dict

    try:
        # Delegate to a more specific function that knows how to load
        # a single component of a specific type
        return await get_single_component_dict(component_type, component_name, components_paths)
    except (ImportError, ModuleNotFoundError) as e:
        # Handle issues with importing the component or its dependencies
        await logger.aerror(f"Import error loading component {component_type}:{component_name}: {e!s}")
        return None
    except (AttributeError, TypeError) as e:
        # Handle issues with component structure or type errors
        await logger.aerror(f"Component structure error for {component_type}:{component_name}: {e!s}")
        return None
    except FileNotFoundError as e:
        # Handle missing files
        await logger.aerror(f"File not found for component {component_type}:{component_name}: {e!s}")
        return None
    except ValueError as e:
        # Handle invalid values or configurations
        await logger.aerror(f"Invalid configuration for component {component_type}:{component_name}: {e!s}")
        return None
    except (KeyError, IndexError) as e:
        # Handle data structure access errors
        await logger.aerror(f"Data structure error for component {component_type}:{component_name}: {e!s}")
        return None
    except RuntimeError as e:
        # Handle runtime errors
        await logger.aerror(f"Runtime error loading component {component_type}:{component_name}: {e!s}")
        await logger.adebug("Full traceback for runtime error", exc_info=True)
        return None
    except OSError as e:
        # Handle OS-related errors (file system, permissions, etc.)
        await logger.aerror(f"OS error loading component {component_type}:{component_name}: {e!s}")
        return None