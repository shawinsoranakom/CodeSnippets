def to_prompt_text(self) -> str:
        """Format reflection for inclusion in prompts."""
        # If verbal format, return the verbal reflection directly
        if self.reflection_format == "verbal" and self.verbal_reflection:
            score_text = (
                f" [score: {self.evaluation_score:.2f}]"
                if self.evaluation_score is not None
                else ""
            )
            return f"Reflection{score_text}: {self.verbal_reflection}"

        # Structured format
        status = "succeeded" if self.success else "failed"
        text = f"Action '{self.action_name}' {status}: {self.result_summary}"
        if self.what_went_wrong:
            text += f"\n  - Issue: {self.what_went_wrong}"
        if self.what_to_do_differently:
            text += f"\n  - Lesson: {self.what_to_do_differently}"
        if self.evaluation_score is not None:
            text += f"\n  - Score: {self.evaluation_score:.2f}"
        return text