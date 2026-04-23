def _fix_missing_equals_in_function_tag(self, chunk: str) -> str:
        """
        Fix missing = in function tags: <function xxx> or <functionxxx>
        Examples:
          <function execute_bash> -> <function=execute_bash>
          <functionexecute_bash> -> <function=execute_bash>
        Only fixes if function name exists in tool definition
        """
        # already correct
        if "<function=" in chunk:
            return chunk

        # Pattern 1: <function xxx> (with space/newline but no =)
        pattern1 = r"<function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>"
        match1 = re.search(pattern1, chunk)
        if match1:
            func_name = match1.group(1).strip()
            # must validate function name exists before fixing
            if func_name and self._validate_function_name(func_name):
                original = match1.group(0)
                fixed = f"<function={func_name}>"
                chunk = chunk.replace(original, fixed, 1)
                return chunk

        # Pattern 2: <functionxxx> (no space, no =)
        # only match <function followed by letters
        pattern2 = r"<function([a-zA-Z_][a-zA-Z0-9_]*)\s*>"
        match2 = re.search(pattern2, chunk)
        if match2:
            func_name = match2.group(1).strip()
            # must validate function name exists before fixing
            if func_name and self._validate_function_name(func_name):
                original = match2.group(0)
                fixed = f"<function={func_name}>"
                chunk = chunk.replace(original, fixed, 1)
                return chunk

        return chunk