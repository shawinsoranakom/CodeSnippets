def simple_split_task(main_task: str) -> list[str]:
	"""Simple fallback: split task by common separators"""
	task_lower = main_task.lower()

	# Try to split by common separators
	if ' and ' in task_lower:
		parts = main_task.split(' and ')
		return [part.strip() for part in parts if part.strip()]
	elif ', ' in main_task:
		parts = main_task.split(', ')
		return [part.strip() for part in parts if part.strip()]
	elif ',' in main_task:
		parts = main_task.split(',')
		return [part.strip() for part in parts if part.strip()]

	# If no separators found, return the original task
	return [main_task]