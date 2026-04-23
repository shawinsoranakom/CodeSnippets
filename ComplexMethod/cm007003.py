def _extract_structured_data(self) -> dict | list:
        """Extract structured data from Data or DataFrame input(s)."""
        if isinstance(self.data, DataFrame):
            return self.data.to_dict(orient="records")

        if hasattr(self.data, "data"):
            return self.data.data

        if not isinstance(self.data, list):
            return self.data

        combined_data: list[dict] = []
        for item in self.data:
            if isinstance(item, DataFrame):
                combined_data.extend(item.to_dict(orient="records"))
            elif hasattr(item, "data"):
                if isinstance(item.data, dict):
                    combined_data.append(item.data)
                elif isinstance(item.data, list):
                    combined_data.extend(item.data)

        if len(combined_data) == 1 and isinstance(combined_data[0], dict):
            return combined_data[0]
        if len(combined_data) == 0:
            return {}
        return combined_data