def wrapper(*args, **kwargs):
            instance = args[0] if args and (hasattr(func, "__self__") and func.__self__ is not None) else None
            is_method = instance is not None

            if is_method and hasattr(instance, "tracer"):
                tracer = instance.tracer
            else:
                tracer = get_tracer(f"transformers.{func.__module__}.{func.__name__}")

            name = span_name or func.__name__
            span_fn = tracer.start_span if standalone else tracer.start_as_current_span
            with span_fn(name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                span.set_attribute("function.is_method", is_method)

                if args:
                    for i, arg in enumerate(args):
                        if isinstance(arg, (str, int, float, bool)) or arg is None:
                            span.set_attribute(f"args.{i}", str(arg))
                        else:
                            span.set_attribute(f"args.{i}", str(type(arg)))
                if kwargs:
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            span.set_attribute(f"kwargs.{key}", str(value))
                        else:
                            span.set_attribute(f"kwargs.{key}", str(type(value)))

                if additional_attributes and is_method:
                    for attr_config in additional_attributes:
                        instance_attribute_name, span_attribute_key, value_or_transform_function = attr_config
                        if hasattr(instance, instance_attribute_name):
                            attribute_value = getattr(instance, instance_attribute_name)
                            if callable(value_or_transform_function):
                                transformed_value = value_or_transform_function(attribute_value)
                            else:
                                transformed_value = value_or_transform_function
                            span.set_attribute(span_attribute_key, transformed_value)

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                    raise