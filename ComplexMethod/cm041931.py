def check_solution(self, solution, test, entry_point):
        solution = sanitize(code=solution, entrypoint=entry_point)
        try:
            global_dict = {
                "math": __import__("math"),
                "hashlib": __import__("hashlib"),
                "re": __import__("re"),
                "List": List,
                "Dict": Dict,
                "Tuple": Tuple,
                "Optional": Optional,
                "Any": Any,
            }

            # Add handling for special cases
            if entry_point == "decode_cyclic":
                solution = (
                    '\n\ndef encode_cyclic(s: str):\n    """\n    returns encoded string by cycling groups of three characters.\n    """\n    # split string to groups. Each of length 3.\n    groups = [s[(3 * i):min((3 * i + 3), len(s))] for i in range((len(s) + 2) // 3)]\n    # cycle elements in each group. Unless group has fewer elements than 3.\n    groups = [(group[1:] + group[0]) if len(group) == 3 else group for group in groups]\n    return "".join(groups)'
                    + "\n\n"
                    + solution
                )
            elif entry_point == "decode_shift":
                solution = (
                    '\n\ndef encode_shift(s: str):\n    """\n    returns encoded string by shifting every character by 5 in the alphabet.\n    """\n    return "".join([chr(((ord(ch) + 5 - ord("a")) % 26) + ord("a")) for ch in s])\n\n\n'
                    + solution
                )
            elif entry_point == "find_zero":
                solution = (
                    "\n\ndef poly(xs: list, x: float):\n    return sum(coeff * (x ** i) for i, coeff in enumerate(xs))\n\n"
                    + solution
                )

            exec(solution, global_dict)

            if entry_point not in global_dict:
                raise ValueError(f"Function {entry_point} is not defined in the solution.")

            exec(test, global_dict)

            check = global_dict["check"]

            result = self.run_with_timeout(check, (global_dict[entry_point],), 15)

            if result is None:
                result = (self.PASS, "The solution passed all test cases.")

        except self.TimeoutError:
            result = (
                self.FAIL,
                "Execution timed out. Please check if your solution contains infinite loops or overly time-consuming operations.",
            )
        except Exception as e:
            error_message = f"Error: {str(e)}.\n Solution: {solution}.\n Test: {test}"
            result = (self.FAIL, error_message)

            with open("error.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")

        return result