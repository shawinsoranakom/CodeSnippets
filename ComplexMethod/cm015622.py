def test_logic(sess, initial):
            output = initial
            # Step until we hit the CALL that invokes the compiled graph
            # function (forward), skipping instrumentation calls
            # (record_pregraph_bytecode_enter/exit).
            if sys.version_info >= (3, 12):
                call_pattern = r">>>.*\[\s*\d+\]:\s*CALL\b"
            elif sys.version_info >= (3, 11):
                call_pattern = r">>>.*\[\s*\d+\]:\s*PRECALL\b"
            else:
                call_pattern = r">>>.*\[\s*\d+\]:\s*CALL_FUNCTION\b"
            while True:
                while not re.search(call_pattern, output):
                    output = yield "s"
                stack_output = yield "stack"
                if "forward" in stack_output and "record_pregraph" not in stack_output:
                    break
                output = yield "s"

            # Extract just the stack lines (skip prompt)
            lines = [
                l for l in stack_output.split("\n") if l.strip() and "(bdb)" not in l
            ]
            stack_at_call = "\n".join(lines)

            # Normalize addresses and tensor values
            stack_at_call = re.sub(r"0x[0-9a-f]+(?! <NULL>)", "0xADDR", stack_at_call)
            stack_at_call = re.sub(r"tensor\([^)]+\)", "tensor(...)", stack_at_call)

            if sys.version_info >= (3, 13):
                self.assertExpectedInline(
                    stack_at_call,
                    """\
Stack (TOS at end):
  [0] 0xADDR <function forward at 0xADDR>
  [1] 0x0 <NULL>
  [2] 0xADDR tensor(...)""",
                )
            elif sys.version_info >= (3, 11):
                self.assertExpectedInline(
                    stack_at_call,
                    """\
Stack (TOS at end):
  [0] 0x0 <NULL>
  [1] 0xADDR <function forward at 0xADDR>
  [2] 0xADDR tensor(...)""",
                )
            else:
                # Python 3.10
                self.assertExpectedInline(
                    stack_at_call,
                    """\
Stack (TOS at end):
  [0] 0xADDR <function forward at 0xADDR>
  [1] 0xADDR tensor(...)""",
                )