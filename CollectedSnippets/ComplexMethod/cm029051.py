async def create_subtasks(main_task: str, llm) -> list[str]:
	"""
	Use LLM to break down main task into logical subtasks

	Real examples of how this works:

	Input: "what is the revenue of nvidia, microsoft, tesla"
	Output: [
	    "Find Nvidia's current revenue and financial data",
	    "Find Microsoft's current revenue and financial data",
	    "Find Tesla's current revenue and financial data"
	]

	Input: "what are ages of musk, altman, bezos, gates"
	Output: [
	    "Find Elon Musk's age and birth date",
	    "Find Sam Altman's age and birth date",
	    "Find Jeff Bezos's age and birth date",
	    "Find Bill Gates's age and birth date"
	]

	Input: "what is the population of tokyo, new york, london, paris"
	Output: [
	    "Find Tokyo's current population",
	    "Find New York's current population",
	    "Find London's current population",
	    "Find Paris's current population"
	]

	Input: "name top 10 yc companies by revenue"
	Output: [
	    "Research Y Combinator's top companies by revenue",
	    "Find revenue data for top YC companies",
	    "Compile list of top 10 YC companies by revenue"
	]
	"""

	prompt = f"""
    Break down this main task into individual, separate subtasks where each subtask focuses on ONLY ONE specific person, company, or item:

    Main task: {main_task}

    RULES:
    - Each subtask must focus on ONLY ONE person/company/item
    - Do NOT combine multiple people/companies/items in one subtask
    - Each subtask should be completely independent
    - If the main task mentions multiple items, create one subtask per item

    Return only the subtasks, one per line, without numbering or bullets.
    Each line should focus on exactly ONE person/company/item.
    """

	try:
		# Use the correct method for ChatGoogle
		response = await llm.ainvoke(prompt)

		# Debug: Print the response type and content
		print(f'DEBUG: Response type: {type(response)}')
		print(f'DEBUG: Response content: {response}')

		# Handle different response types - ChatGoogle returns string content
		if hasattr(response, 'content'):
			content = response.content
		elif isinstance(response, str):
			content = response
		elif hasattr(response, 'text'):
			content = response.text
		else:
			# Convert to string if it's some other type
			content = str(response)

		# Split by newlines and clean up
		subtasks = [task.strip() for task in content.strip().split('\n') if task.strip()]

		# Remove any numbering or bullets that the LLM might add
		cleaned_subtasks = []
		for task in subtasks:
			# Remove common prefixes like "1. ", "- ", "* ", etc.
			cleaned = task.lstrip('0123456789.-* ')
			if cleaned:
				cleaned_subtasks.append(cleaned)

		return cleaned_subtasks if cleaned_subtasks else simple_split_task(main_task)
	except Exception as e:
		print(f'Error creating subtasks: {e}')
		# Fallback to simple split
		return simple_split_task(main_task)