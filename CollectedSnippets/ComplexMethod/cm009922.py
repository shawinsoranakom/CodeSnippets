def map(self, example: Example) -> dict[str, str]:
        """Maps the Example, or dataset row to a dictionary."""
        if not example.outputs:
            msg = f"Example {example.id} has no outputs to use as a reference."
            raise ValueError(msg)
        if self.reference_key is None:
            if len(example.outputs) > 1:
                msg = (
                    f"Example {example.id} has multiple outputs, so you must"
                    " specify a reference_key."
                )
                raise ValueError(msg)
            output = next(iter(example.outputs.values()))
        elif self.reference_key not in example.outputs:
            msg = (
                f"Example {example.id} does not have reference key"
                f" {self.reference_key}."
            )
            raise ValueError(msg)
        else:
            output = example.outputs[self.reference_key]
        return {
            "reference": self.serialize_chat_messages([output])
            if isinstance(output, dict) and output.get("type") and output.get("data")
            else output,
        }