async def normalized_wrapper(*args, params: BaseModel | None = None, **kwargs):
			"""Normalized action that only accepts kwargs"""
			# Validate no positional args
			if args:
				raise TypeError(f'{func.__name__}() does not accept positional arguments, only keyword arguments are allowed')

			# Prepare arguments for original function
			call_args = []
			call_kwargs = {}

			# Handle Type 1 pattern (first arg is the param model)
			if param_model_provided and parameters and parameters[0].name not in special_param_names:
				if params is None:
					raise ValueError(f"{func.__name__}() missing required 'params' argument")
				# For Type 1, we'll use the params object as first argument
				pass
			else:
				# Type 2 pattern - need to unpack params
				# If params is None, try to create it from kwargs
				if params is None and action_params:
					# Extract action params from kwargs
					action_kwargs = {}
					for param in action_params:
						if param.name in kwargs:
							action_kwargs[param.name] = kwargs[param.name]
					if action_kwargs:
						# Use the param_model which has the correct types defined
						params = param_model(**action_kwargs)

			# Build call_args by iterating through original function parameters in order
			params_dict = params.model_dump() if params is not None else {}

			for i, param in enumerate(parameters):
				# Skip first param for Type 1 pattern (it's the model itself)
				if param_model_provided and i == 0 and param.name not in special_param_names:
					call_args.append(params)
				elif param.name in special_param_names:
					# This is a special parameter
					if param.name in kwargs:
						value = kwargs[param.name]
						# Check if required special param is None
						if value is None and param.default == Parameter.empty:
							if param.name == 'browser_session':
								raise ValueError(f'Action {func.__name__} requires browser_session but none provided.')
							elif param.name == 'page_extraction_llm':
								raise ValueError(f'Action {func.__name__} requires page_extraction_llm but none provided.')
							elif param.name == 'file_system':
								raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
							elif param.name == 'page':
								raise ValueError(f'Action {func.__name__} requires page but none provided.')
							elif param.name == 'available_file_paths':
								raise ValueError(f'Action {func.__name__} requires available_file_paths but none provided.')
							elif param.name == 'file_system':
								raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
							else:
								raise ValueError(f"{func.__name__}() missing required special parameter '{param.name}'")
						call_args.append(value)
					elif param.default != Parameter.empty:
						call_args.append(param.default)
					else:
						# Special param is required but not provided
						if param.name == 'browser_session':
							raise ValueError(f'Action {func.__name__} requires browser_session but none provided.')
						elif param.name == 'page_extraction_llm':
							raise ValueError(f'Action {func.__name__} requires page_extraction_llm but none provided.')
						elif param.name == 'file_system':
							raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
						elif param.name == 'page':
							raise ValueError(f'Action {func.__name__} requires page but none provided.')
						elif param.name == 'available_file_paths':
							raise ValueError(f'Action {func.__name__} requires available_file_paths but none provided.')
						elif param.name == 'file_system':
							raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
						else:
							raise ValueError(f"{func.__name__}() missing required special parameter '{param.name}'")
				else:
					# This is an action parameter
					if param.name in params_dict:
						call_args.append(params_dict[param.name])
					elif param.default != Parameter.empty:
						call_args.append(param.default)
					else:
						raise ValueError(f"{func.__name__}() missing required parameter '{param.name}'")

			# Call original function with positional args
			if iscoroutinefunction(func):
				return await func(*call_args)
			else:
				return await asyncio.to_thread(func, *call_args)