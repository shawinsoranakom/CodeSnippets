def _construct_prompts(self, text: str | list[str]) -> list[str]:
        """
        Construct prompts by replacing task tokens with corresponding prompt strings.
        """
        if isinstance(text, str):
            text = [text]

        prompts = []
        for prompt in text:
            # Check for tasks without inputs
            for task_token, task_prompt in self.task_prompts_without_inputs.items():
                if task_token in prompt:
                    if prompt != task_token:
                        raise ValueError(f"Task token {task_token} should be the only content in the prompt.")
                    prompt = task_prompt
                    break
            # Check for tasks with inputs
            for task_token, task_prompt in self.task_prompts_with_input.items():
                if task_token in prompt:
                    input_text = prompt.replace(task_token, "").strip()
                    prompt = task_prompt.format(input=input_text)
                    break
            prompts.append(prompt)
        return prompts