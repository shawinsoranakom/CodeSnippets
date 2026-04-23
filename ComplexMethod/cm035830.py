def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        """Execute IPython code using E2B's code interpreter."""
        if self.sandbox is None:
            return ErrorObservation("E2B sandbox not initialized")

        try:
            result = self.sandbox.sandbox.run_code(action.code)

            outputs = []
            if hasattr(result, 'results') and result.results:
                for r in result.results:
                    if hasattr(r, 'text') and r.text:
                        outputs.append(r.text)
                    elif hasattr(r, 'html') and r.html:
                        outputs.append(r.html)
                    elif hasattr(r, 'png') and r.png:
                        outputs.append(f"[Image data: {len(r.png)} bytes]")

            if hasattr(result, 'error') and result.error:
                return ErrorObservation(f"IPython error: {result.error}")

            return IPythonRunCellObservation(
                content='\n'.join(outputs) if outputs else '',
                code=action.code
            )
        except Exception as e:
            return ErrorObservation(f"Failed to execute IPython code: {e}")