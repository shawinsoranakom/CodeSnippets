def send_command(self, command=None, prompt=None, answer=None, sendonly=False, newline=True, prompt_retry_check=False, check_all=False):
        """Executes a command over the device connection

        This method will execute a command over the device connection and
        return the results to the caller.  This method will also perform
        logging of any commands based on the `nolog` argument.

        :param command: The command to send over the connection to the device
        :param prompt: A single regex pattern or a sequence of patterns to evaluate the expected prompt from the command
        :param answer: The answer to respond with if the prompt is matched.
        :param sendonly: Bool value that will send the command but not wait for a result.
        :param newline: Bool value that will append the newline character to the command
        :param prompt_retry_check: Bool value for trying to detect more prompts
        :param check_all: Bool value to indicate if all the values in prompt sequence should be matched or any one of
                          given prompt.
        :returns: The output from the device after executing the command
        """
        kwargs = {
            'command': to_bytes(command),
            'sendonly': sendonly,
            'newline': newline,
            'prompt_retry_check': prompt_retry_check,
            'check_all': check_all
        }

        if prompt is not None:
            if isinstance(prompt, list):
                kwargs['prompt'] = [to_bytes(p) for p in prompt]
            else:
                kwargs['prompt'] = to_bytes(prompt)
        if answer is not None:
            if isinstance(answer, list):
                kwargs['answer'] = [to_bytes(p) for p in answer]
            else:
                kwargs['answer'] = to_bytes(answer)

        resp = self._connection.send(**kwargs)

        if not self.response_logging:
            self.history.append(('*****', '*****'))
        else:
            self.history.append((kwargs['command'], resp))

        return resp