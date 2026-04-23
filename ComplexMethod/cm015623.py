def test_logic(sess, initial):
            output = initial
            # Step until we hit the CALL that invokes the compiled graph
            # function. See test_stack_command for details.
            if sys.version_info >= (3, 12):
                call_pattern = r">>>.*\[\s*\d+\]:\s*CALL\b"
            elif sys.version_info >= (3, 11):
                call_pattern = r">>>.*\[\s*\d+\]:\s*PRECALL\b"
            else:
                call_pattern = r">>>.*\[\s*\d+\]:\s*CALL_FUNCTION\b"
            while True:
                while not re.search(call_pattern, output):
                    output = yield "s"
                stack_output = yield "__stack__"
                if "forward" in stack_output and "record_pregraph" not in stack_output:
                    break
                output = yield "s"

            # Normalize addresses and tensor values
            normalized = re.sub(r"0x[0-9a-f]+", "0xADDR", stack_output)
            normalized = re.sub(r"tensor\([^)]+\)", "tensor(...)", normalized)
            # Extract just the list part
            match = re.search(r"\[.*\]", normalized, re.DOTALL)
            self.assertIsNotNone(match)
            stack_list = match.group(0)

            if sys.version_info >= (3, 13):
                self.assertExpectedInline(
                    stack_list,
                    """[<function forward at 0xADDR>, <NULL>, tensor(...)]""",
                )
            elif sys.version_info >= (3, 11):
                self.assertExpectedInline(
                    stack_list,
                    """[<NULL>, <function forward at 0xADDR>, tensor(...)]""",
                )
            else:
                # Python 3.10
                self.assertExpectedInline(
                    stack_list,
                    """[<function forward at 0xADDR>, tensor(...)]""",
                )