def _retrieve_option(self, args: Dict[str, Any]) -> ToolExecutionResult:
        raw_option_number = args.get("option_number")
        raw_index = args.get("index")

        def coerce_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        option_number = coerce_int(raw_option_number)
        index = coerce_int(raw_index)

        if option_number is None and index is None:
            return ToolExecutionResult(
                ok=False,
                result={"error": "retrieve_option requires option_number"},
                summary={"error": "Missing option_number"},
            )

        resolved_index = index if option_number is None else option_number - 1
        if resolved_index is None:
            return ToolExecutionResult(
                ok=False,
                result={"error": "Invalid option_number"},
                summary={"error": "Invalid option_number"},
            )

        if resolved_index < 0 or resolved_index >= len(self.option_codes):
            return ToolExecutionResult(
                ok=False,
                result={
                    "error": "Option index out of range",
                    "option_number": resolved_index + 1,
                    "available": len(self.option_codes),
                },
                summary={
                    "error": "Option index out of range",
                    "available": len(self.option_codes),
                },
            )

        code = ensure_str(self.option_codes[resolved_index])
        if not code.strip():
            return ToolExecutionResult(
                ok=False,
                result={
                    "error": "Option code is empty or unavailable",
                    "option_number": resolved_index + 1,
                },
                summary={"error": "Option code unavailable"},
            )

        summary = {
            "option_number": resolved_index + 1,
            "contentLength": len(code),
            "preview": summarize_text(code, 200),
        }
        result = {"option_number": resolved_index + 1, "code": code}
        return ToolExecutionResult(ok=True, result=result, summary=summary)