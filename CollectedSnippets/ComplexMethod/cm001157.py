def _validate_no_prisma_objects(obj: Any, path: str = "result") -> None:
    """
    Recursively validate that no Prisma objects are being returned from service methods.
    This enforces proper separation of layers - only application models should cross service boundaries.
    """
    if obj is None:
        return

    # Check if it's a Prisma model object
    if hasattr(obj, "__class__") and hasattr(obj.__class__, "__module__"):
        module_name = obj.__class__.__module__
        if module_name and "prisma.models" in module_name:
            raise ValueError(
                f"Prisma object {obj.__class__.__name__} found in {path}. "
                "Service methods must return application models, not Prisma objects. "
                f"Use {obj.__class__.__name__}.from_db() to convert to application model."
            )

    # Recursively check collections
    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            _validate_no_prisma_objects(item, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            _validate_no_prisma_objects(value, f"{path}['{key}']")