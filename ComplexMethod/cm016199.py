def parse_junit_reports(path_to_reports: str) -> list[TestCase]:  # type: ignore[no-any-unimported]
    def parse_file(path: str) -> list[TestCase]:  # type: ignore[no-any-unimported]
        try:
            return convert_junit_to_testcases(JUnitXml.fromfile(path))
        except Exception as err:
            rich.print(
                f":Warning: [yellow]Warning[/yellow]: Failed to read {path}: {err}"
            )
            return []

    if not os.path.exists(path_to_reports):
        raise FileNotFoundError(f"Path '{path_to_reports}', not found")
    # Return early if the path provided is just a file
    if os.path.isfile(path_to_reports):
        return parse_file(path_to_reports)
    ret_xml = []
    if os.path.isdir(path_to_reports):
        for root, _, files in os.walk(path_to_reports):
            for fname in [f for f in files if f.endswith("xml")]:
                ret_xml += parse_file(os.path.join(root, fname))
    return ret_xml