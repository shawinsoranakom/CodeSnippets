def _extract_all_params(func: Callable, args: tuple, kwargs: dict) -> dict[str, Any]:
	"""Extract all parameters including explicit params and closure variables

	Args:
		func: The function being decorated
		args: Positional arguments passed to the function
		kwargs: Keyword arguments passed to the function

	Returns:
		Dictionary of all parameters {name: value}
	"""
	sig = inspect.signature(func)
	bound_args = sig.bind_partial(*args, **kwargs)
	bound_args.apply_defaults()

	all_params: dict[str, Any] = {}

	# 1. Extract explicit parameters (skip 'browser' and 'self')
	for param_name, param_value in bound_args.arguments.items():
		if param_name == 'browser':
			continue
		if param_name == 'self' and hasattr(param_value, '__dict__'):
			# Extract self attributes as individual variables
			for attr_name, attr_value in param_value.__dict__.items():
				all_params[attr_name] = attr_value
		else:
			all_params[param_name] = param_value

	# 2. Extract closure variables
	if func.__closure__:
		closure_vars = func.__code__.co_freevars
		closure_values = [cell.cell_contents for cell in func.__closure__]

		for name, value in zip(closure_vars, closure_values):
			# Skip if already captured from explicit params
			if name in all_params:
				continue
			# Special handling for 'self' in closures
			if name == 'self' and hasattr(value, '__dict__'):
				for attr_name, attr_value in value.__dict__.items():
					if attr_name not in all_params:
						all_params[attr_name] = attr_value
			else:
				all_params[name] = value

	# 3. Extract referenced globals (like logger, module-level vars, etc.)
	#    Let cloudpickle handle serialization instead of special-casing
	for name in func.__code__.co_names:
		if name in all_params:
			continue
		if name in func.__globals__:
			all_params[name] = func.__globals__[name]

	return all_params