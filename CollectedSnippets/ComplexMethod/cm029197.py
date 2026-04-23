def extract_type_names(annotation):
		"""Recursively extract all type names from annotation"""
		if annotation is None or annotation == inspect.Parameter.empty:
			return

		# Handle Pydantic generics (e.g., AgentHistoryList[MyModel]) - check this FIRST
		# Pydantic generics have __pydantic_generic_metadata__ with 'origin' and 'args'
		pydantic_meta = getattr(annotation, '__pydantic_generic_metadata__', None)
		if pydantic_meta and pydantic_meta.get('origin'):
			# Add the origin class name (e.g., 'AgentHistoryList')
			origin_class = pydantic_meta['origin']
			if hasattr(origin_class, '__name__'):
				referenced_names.add(origin_class.__name__)
			# Recursively extract from generic args (e.g., MyModel)
			for arg in pydantic_meta.get('args', ()):
				extract_type_names(arg)
			return

		# Handle simple types with __name__
		if hasattr(annotation, '__name__'):
			referenced_names.add(annotation.__name__)

		# Handle string annotations
		if isinstance(annotation, str):
			referenced_names.add(annotation)

		# Handle generic types like Union[X, Y], Literal['x'], etc.
		origin = get_origin(annotation)
		args = get_args(annotation)

		if origin:
			# Add the origin type name (e.g., 'Union', 'Literal')
			if hasattr(origin, '__name__'):
				referenced_names.add(origin.__name__)

		# Recursively extract from generic args
		if args:
			for arg in args:
				extract_type_names(arg)