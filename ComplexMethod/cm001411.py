def format(self):
        step = f"Executed `{self.action.use_tool}`\n"
        reasoning = (
            _r.summary()
            if isinstance(_r := self.action.thoughts, ModelWithSummary)
            else _r
        )
        step += f'- **Reasoning:** "{reasoning}"\n'
        step += (
            "- **Status:** "
            f"`{self.result.status if self.result else 'did_not_finish'}`\n"
        )
        if self.result:
            if self.result.status == "success":
                result = str(self.result)
                result = "\n" + indent(result) if "\n" in result else result
                step += f"- **Output:** {result}"
            elif self.result.status == "error":
                step += f"- **Reason:** {self.result.reason}\n"
                if self.result.error:
                    step += f"- **Error:** {self.result.error}\n"
            elif self.result.status == "interrupted_by_human":
                step += f"- **Feedback:** {self.result.feedback}\n"
        return step