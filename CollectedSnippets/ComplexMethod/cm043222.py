def _compile_c4a_script(self):
        """Compile C4A script to JavaScript"""
        try:
            # Try importing the compiler
            try:
                from .script import compile
            except ImportError:
                from crawl4ai.script import compile

            # Handle both string and list inputs
            if isinstance(self.c4a_script, str):
                scripts = [self.c4a_script]
            else:
                scripts = self.c4a_script

            # Compile each script
            compiled_js = []
            for i, script in enumerate(scripts):
                result = compile(script)

                if result.success:
                    compiled_js.extend(result.js_code)
                else:
                    # Format error message following existing patterns
                    error = result.first_error
                    error_msg = (
                        f"C4A Script compilation error (script {i+1}):\n"
                        f"  Line {error.line}, Column {error.column}: {error.message}\n"
                        f"  Code: {error.source_line}"
                    )
                    if error.suggestions:
                        error_msg += f"\n  Suggestion: {error.suggestions[0].message}"

                    raise ValueError(error_msg)

            self.js_code = compiled_js

        except ImportError:
            raise ValueError(
                "C4A script compiler not available. "
                "Please ensure crawl4ai.script module is properly installed."
            )
        except Exception as e:
            # Re-raise with context
            if "compilation error" not in str(e).lower():
                raise ValueError(f"Failed to compile C4A script: {str(e)}")
            raise