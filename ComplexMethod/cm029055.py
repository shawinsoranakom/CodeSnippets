def provider(self) -> str:
		"""Return the provider name based on the LangChain model class."""
		model_class_name = self.chat.__class__.__name__.lower()
		if 'openai' in model_class_name:
			return 'openai'
		elif 'anthropic' in model_class_name or 'claude' in model_class_name:
			return 'anthropic'
		elif 'google' in model_class_name or 'gemini' in model_class_name:
			return 'google'
		elif 'groq' in model_class_name:
			return 'groq'
		elif 'ollama' in model_class_name:
			return 'ollama'
		elif 'deepseek' in model_class_name:
			return 'deepseek'
		else:
			return 'langchain'