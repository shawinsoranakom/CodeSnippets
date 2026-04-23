def format_for_prompt(self) -> str:
        """Format the context for inclusion in prompts."""
        lines = []

        if self.extracted_variables:
            lines.append("## Extracted Variables")
            for var in self.extracted_variables:
                if var.value is not None:
                    lines.append(
                        f"- {var.name} = {var.value} {var.unit}: {var.description}"
                    )
                else:
                    lines.append(f"- {var.name}: {var.description}")
            lines.append("")

        if self.calculation_steps:
            lines.append("## Calculations Performed")
            for calc in self.calculation_steps:
                status = "valid" if calc.is_valid else "INVALID"
                lines.append(f"- {calc.expression} = {calc.result} [{status}]")
                if calc.verification_method:
                    lines.append(f"  Verified by: {calc.verification_method}")
            lines.append("")

        return "\n".join(lines) if lines else ""