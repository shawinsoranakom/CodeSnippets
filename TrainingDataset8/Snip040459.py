def main() -> None:
    if len(sys.argv) != 2:
        raise Exception(f'Specify project name, e.g: "{sys.argv[0]} streamlit-nightly"')
    project_name = sys.argv[1]
    update_files(project_name, FILES_AND_REGEXES)