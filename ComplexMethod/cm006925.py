def extract_data(self, result):
        """Extract the data from the result. this is where the self.status is set."""
        if isinstance(result, Message):
            self.status = result.get_text()
            return (
                self.status if self.status is not None else "No text available"
            )  # Provide a default message if .text_key is missing
        # IMPORTANT: keep this before the generic `hasattr(result, "data")` branch.
        # pandas objects expose a `.data` attribute, but for DataFrame/Series we must
        # preserve the object rather than returning its underlying array/manager.
        if isinstance(result, pd.DataFrame | pd.Series):
            return result
        if hasattr(result, "data"):
            return result.data
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if isinstance(result, Data | dict | str):
            return result.data if isinstance(result, Data) else result

        if self.status:
            return self.status
        return result