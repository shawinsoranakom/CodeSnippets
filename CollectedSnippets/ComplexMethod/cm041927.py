def get_choice_function_arguments(self, rsp: ChatCompletion) -> dict:
        """Required to provide the first function arguments of choice.

        :param dict rsp: same as in self.get_choice_function(rsp)
        :return dict: return the first function arguments of choice, for example,
            {'language': 'python', 'code': "print('Hello, World!')"}
        """
        message = rsp.choices[0].message
        if (
            message.tool_calls is not None
            and message.tool_calls[0].function is not None
            and message.tool_calls[0].function.arguments is not None
        ):
            # reponse is code
            try:
                return json.loads(message.tool_calls[0].function.arguments, strict=False)
            except json.decoder.JSONDecodeError as e:
                error_msg = (
                    f"Got JSONDecodeError for \n{'--'*40} \n{message.tool_calls[0].function.arguments}, {str(e)}"
                )
                logger.error(error_msg)
                return self._parse_arguments(message.tool_calls[0].function.arguments)
        elif message.tool_calls is None and message.content is not None:
            # reponse is code, fix openai tools_call respond bug,
            # The response content is `code``, but it appears in the content instead of the arguments.
            code_formats = "```"
            if message.content.startswith(code_formats) and message.content.endswith(code_formats):
                code = CodeParser.parse_code(text=message.content)
                return {"language": "python", "code": code}
            # reponse is message
            return {"language": "markdown", "code": self.get_choice_text(rsp)}
        else:
            logger.error(f"Failed to parse \n {rsp}\n")
            raise Exception(f"Failed to parse \n {rsp}\n")