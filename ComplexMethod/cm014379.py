def parse_output(fpath: str, inclusive: bool) -> FunctionCounts:
                _annotate_invocation, annotate_invocation_output = run([
                    "callgrind_annotate",
                    f"--inclusive={'yes' if inclusive else 'no'}",
                    "--threshold=100",
                    "--show-percs=no",
                    fpath
                ], check=True)

                total_pattern = re.compile(r"^([0-9,]+)\s+PROGRAM TOTALS")
                begin_pattern = re.compile(r"Ir\s+file:function")
                function_pattern = re.compile(r"^\s*([0-9,]+)\s+(.+:.+)$")

                class ScanState(enum.Enum):
                    SCANNING_FOR_TOTAL = 0
                    SCANNING_FOR_START = 1
                    PARSING = 2

                scan_state = ScanState.SCANNING_FOR_TOTAL
                fn_counts = []
                for l in annotate_invocation_output.splitlines(keepends=False):
                    if scan_state == ScanState.SCANNING_FOR_TOTAL:
                        total_match = total_pattern.match(l)
                        if total_match:
                            program_totals = int(total_match.groups()[0].replace(",", ""))
                            scan_state = ScanState.SCANNING_FOR_START

                    elif scan_state == ScanState.SCANNING_FOR_START:
                        if begin_pattern.match(l):
                            scan_state = ScanState.PARSING

                    else:
                        if scan_state != ScanState.PARSING:
                            raise AssertionError("Failed to enter PARSING state while parsing callgrind_annotate output")
                        fn_match = function_pattern.match(l)
                        if fn_match:
                            ir_str, file_function = fn_match.groups()
                            ir = int(ir_str.replace(",", ""))
                            if ir == program_totals:  # type: ignore[possibly-undefined]
                                # Callgrind includes some top level red herring symbols when
                                # a program dumps multiple profiles.
                                continue
                            fn_counts.append(FunctionCount(ir, file_function))

                        elif re.match(r"-+", l):
                            # Ignore heading separator lines.
                            continue

                        else:
                            break

                if scan_state != ScanState.PARSING:
                    raise AssertionError(f"Failed to parse {fpath}")
                return FunctionCounts(tuple(sorted(fn_counts, reverse=True)), inclusive=inclusive)