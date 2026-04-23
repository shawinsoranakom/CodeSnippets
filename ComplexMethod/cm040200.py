def model_from_config(config, custom_objects=None):
    """Instantiates a Keras model from its config.

    Args:
        config: Configuration dictionary.
        custom_objects: Optional dictionary mapping names
            (strings) to custom classes or functions to be
            considered during deserialization.

    Returns:
        A Keras model instance (uncompiled).

    Raises:
        TypeError: if `config` is not a dictionary.
    """
    if isinstance(config, list):
        raise TypeError(
            "`model_from_config` expects a dictionary, not a list. "
            f"Received: config={config}. Did you meant to use "
            "`Sequential.from_config(config)`?"
        )

    global MODULE_OBJECTS

    if not hasattr(MODULE_OBJECTS, "ALL_OBJECTS"):
        from keras.src import layers
        from keras.src import models

        MODULE_OBJECTS.ALL_OBJECTS = layers.__dict__
        MODULE_OBJECTS.ALL_OBJECTS["InputLayer"] = layers.InputLayer
        MODULE_OBJECTS.ALL_OBJECTS["Functional"] = models.Functional
        MODULE_OBJECTS.ALL_OBJECTS["Model"] = models.Model
        MODULE_OBJECTS.ALL_OBJECTS["Sequential"] = models.Sequential

    batch_input_shape = config["config"].pop("batch_input_shape", None)
    if batch_input_shape is not None:
        if config["class_name"] == "InputLayer":
            config["config"]["batch_shape"] = batch_input_shape
        else:
            config["config"]["input_shape"] = batch_input_shape

    axis = config["config"].pop("axis", None)
    if axis is not None:
        if isinstance(axis, list) and len(axis) == 1:
            config["config"]["axis"] = int(axis[0])
        elif isinstance(axis, (int, float)):
            config["config"]["axis"] = int(axis)

    # Handle backwards compatibility for Keras lambdas
    if config["class_name"] == "Lambda":
        for dep_arg in LAMBDA_DEP_ARGS:
            _ = config["config"].pop(dep_arg, None)
        function_config = config["config"]["function"]
        if isinstance(function_config, list):
            function_dict = {"class_name": "__lambda__", "config": {}}
            function_dict["config"]["code"] = function_config[0]
            function_dict["config"]["defaults"] = function_config[1]
            function_dict["config"]["closure"] = function_config[2]
            config["config"]["function"] = function_dict

    return serialization.deserialize_keras_object(
        config,
        module_objects=MODULE_OBJECTS.ALL_OBJECTS,
        custom_objects=custom_objects,
        printable_module_name="layer",
    )