def get_profile(filename_or_url, profile_path):
    # i.com/ is a shortcut for openinterpreter.com/profiles/
    shortcuts = ["i.com/", "www.i.com/", "https://i.com/", "http://i.com/"]
    for shortcut in shortcuts:
        if filename_or_url.startswith(shortcut):
            filename_or_url = filename_or_url.replace(
                shortcut, "https://openinterpreter.com/profiles/"
            )
            if "." not in filename_or_url.split("/")[-1]:
                extensions = [".json", ".py", ".yaml"]
                for ext in extensions:
                    try:
                        response = requests.get(filename_or_url + ext)
                        response.raise_for_status()
                        filename_or_url += ext
                        break
                    except requests.exceptions.HTTPError:
                        continue
            break

    profile_path = os.path.join(profile_dir, filename_or_url)
    extension = os.path.splitext(filename_or_url)[-1]

    # Try local
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as file:
            if extension == ".py":
                python_script = file.read()

                # Remove `from interpreter import interpreter` and `interpreter = OpenInterpreter()`, because we handle that before the script
                tree = ast.parse(python_script)
                tree = RemoveInterpreter().visit(tree)
                python_script = ast.unparse(tree)

                return {
                    "start_script": python_script,
                    "version": OI_VERSION,
                }  # Python scripts are always the latest version
            elif extension == ".json":
                return json.load(file)
            else:
                return yaml.safe_load(file)

    # Try URL
    response = requests.get(filename_or_url)
    response.raise_for_status()
    if extension == ".py":
        return {"start_script": response.text, "version": OI_VERSION}
    elif extension == ".json":
        return json.loads(response.text)
    elif extension == ".yaml":
        return yaml.safe_load(response.text)

    raise Exception(f"Profile '{filename_or_url}' not found.")