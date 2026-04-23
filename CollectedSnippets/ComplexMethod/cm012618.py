def wrapped(*args, **kwargs) -> str:
            # Optionally upcast args to float32.
            upcast_args = [maybe_upcast_arg(arg) for arg in args]
            upcast_kwargs = {key: maybe_upcast_arg(val) for key, val in kwargs.items()}

            # Call the decorated function, optionally downcasting the result.
            result = func(*upcast_args, **upcast_kwargs)
            any_needs_upcast = convert_output and any(
                needs_upcast_to_float32(var)
                for var in itertools.chain(args, kwargs.values())
            )
            result_dtype = (
                None
                if not any_needs_upcast
                else getattr(get_dtype_handler(), func.__name__)(*args, **kwargs)
            )
            needs_downcast = result_dtype not in (torch.float32, None)
            downcast_string = (
                f".to({triton_type(result_dtype)})"
                if needs_downcast and result_dtype is not None
                else ""
            )
            return f"{result}{downcast_string}"