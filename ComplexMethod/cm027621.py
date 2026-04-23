def as_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of an intent response."""
        response_dict: dict[str, Any] = {
            "speech": {k: dict(v) for k, v in self.speech.items()},
            "card": {k: dict(v) for k, v in self.card.items()},
            "language": self.language,
            "response_type": self.response_type.value,
        }

        if self.reprompt:
            response_dict["reprompt"] = {k: dict(v) for k, v in self.reprompt.items()}
        if self.speech_slots:
            response_dict["speech_slots"] = self.speech_slots.copy()

        response_data: dict[str, Any] = {}

        if self.response_type == IntentResponseType.ERROR:
            assert self.error_code is not None, "error code is required"
            response_data["code"] = self.error_code.value
        else:
            # action done or query answer
            response_data["success"] = [
                dataclasses.asdict(target) for target in self.success_results
            ]

            response_data["failed"] = [
                dataclasses.asdict(target) for target in self.failed_results
            ]

        response_dict["data"] = response_data

        return response_dict