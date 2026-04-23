def extract_matches(self) -> list[Data]:
        if not self.pattern or not self.input_text:
            self.status = []
            return []

        try:
            # Compile regex pattern
            pattern = re.compile(self.pattern)

            # Find all matches in the input text
            matches = pattern.findall(self.input_text)

            # Filter out empty matches
            filtered_matches = [match for match in matches if match]  # Remove empty matches

            # Return empty list for no matches, or list of matches if found
            result: list = [] if not filtered_matches else [Data(data={"match": match}) for match in filtered_matches]

        except re.error as e:
            error_message = f"Invalid regex pattern: {e!s}"
            result = [Data(data={"error": error_message})]
        except ValueError as e:
            error_message = f"Error extracting matches: {e!s}"
            result = [Data(data={"error": error_message})]

        self.status = result
        return result