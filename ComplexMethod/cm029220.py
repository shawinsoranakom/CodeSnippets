def _recursive_process_list_or_tuple(container: list | tuple, url_replacements: dict[str, str]) -> list | tuple:
		"""Helper method to process lists and tuples."""
		if isinstance(container, tuple):
			# For tuples, create a new tuple with processed items
			processed_items = []
			for item in container:
				if isinstance(item, str):
					processed_items.append(Agent._replace_shortened_urls_in_string(item, url_replacements))
				elif isinstance(item, BaseModel):
					Agent._recursive_process_all_strings_inside_pydantic_model(item, url_replacements)
					processed_items.append(item)
				elif isinstance(item, dict):
					Agent._recursive_process_dict(item, url_replacements)
					processed_items.append(item)
				elif isinstance(item, (list, tuple)):
					processed_items.append(Agent._recursive_process_list_or_tuple(item, url_replacements))
				else:
					processed_items.append(item)
			return tuple(processed_items)
		else:
			# For lists, modify in place
			for i, item in enumerate(container):
				if isinstance(item, str):
					container[i] = Agent._replace_shortened_urls_in_string(item, url_replacements)
				elif isinstance(item, BaseModel):
					Agent._recursive_process_all_strings_inside_pydantic_model(item, url_replacements)
				elif isinstance(item, dict):
					Agent._recursive_process_dict(item, url_replacements)
				elif isinstance(item, (list, tuple)):
					container[i] = Agent._recursive_process_list_or_tuple(item, url_replacements)
			return container