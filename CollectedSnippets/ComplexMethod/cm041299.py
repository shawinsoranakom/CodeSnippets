def __init__(self, namespace: str, name: str, schema_version: int = 1):
        if not namespace or namespace.strip() == "":
            raise ValueError("Namespace must be non-empty string.")
        self._namespace = namespace

        if not name or name.strip() == "":
            raise ValueError("Metric name must be non-empty string.")
        self._name = name

        if schema_version is None:
            raise ValueError("An explicit schema_version is required for Counter metrics")

        if not isinstance(schema_version, int):
            raise TypeError("Schema version must be an integer.")

        if schema_version <= 0:
            raise ValueError("Schema version must be greater than zero.")

        self._schema_version = schema_version