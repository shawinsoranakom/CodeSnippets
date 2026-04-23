def load_db_models():
    """Load database models from api/db/db_models.py"""
    models_path = os.path.join(PROJECT_BASE, 'api', 'db', 'db_models.py')

    if not os.path.exists(models_path):
        raise FileNotFoundError(f"db_models.py not found at {models_path}")

    # Import the module
    spec = importlib.util.spec_from_file_location("db_models", models_path)
    db_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_models)

    # Get all Model subclasses
    models = []
    for name, obj in inspect.getmembers(db_models):
        if inspect.isclass(obj) and issubclass(obj, Model) and obj is not Model:
            # Skip base model classes
            if obj.__name__ in ['BaseModel', 'DataBaseModel']:
                continue
            # Check if it has a database attribute (is a proper model)
            if hasattr(obj._meta, 'database'):
                models.append(obj)

    return models, db_models