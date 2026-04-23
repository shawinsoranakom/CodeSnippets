def checker() -> bool:
        results = []
        try:
            results = pr.load_data("Hello world.", k=1)
        except requests.exceptions.RequestException:
            return False

        if not (
            len(results) == 1
            and results[0].text == "Hello world."
            and EXAMPLE_TEXT_FILE in results[0].metadata["path"]
        ):
            return False

        results = []
        try:
            results = pr.load_data("This is a test.", k=1)
        except requests.exceptions.RequestException:
            return False

        return (
            len(results) == 1
            and results[0].text == "This is a test."
            and EXAMPLE_TEXT_FILE in results[0].metadata["path"]
        )