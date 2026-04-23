def benchmark_tests_list():
    """List benchmark tests command"""
    import glob
    import json
    import os
    import re

    tests = {}

    # Get the directory of this file
    this_dir = os.path.dirname(os.path.abspath(__file__))

    glob_path = os.path.join(
        this_dir,
        "./benchmark/agbenchmark/challenges/**/[!deprecated]*/data.json",
    )
    # Use it as the base for the glob pattern, excluding 'deprecated' directory
    for data_file in glob.glob(glob_path, recursive=True):
        if "deprecated" not in data_file:
            with open(data_file, "r") as f:
                try:
                    data = json.load(f)
                    category = data.get("category", [])
                    test_name = data.get("name", "")
                    if category and test_name:
                        if category[0] not in tests:
                            tests[category[0]] = []
                        tests[category[0]].append(test_name)
                except json.JSONDecodeError:
                    print(f"Error: {data_file} is not a valid JSON file.")
                    continue
                except IOError:
                    print(f"IOError: file could not be read: {data_file}")
                    continue

    if tests:
        click.echo(click.style("Available tests: 📚", fg="green"))
        for category, test_list in tests.items():
            click.echo(click.style(f"\t📖 {category}", fg="blue"))
            for test in sorted(test_list):
                test_name = (
                    " ".join(word for word in re.split("([A-Z][a-z]*)", test) if word)
                    .replace("_", "")
                    .replace("C L I", "CLI")
                    .replace("  ", " ")
                )
                test_name_padded = f"{test_name:<40}"
                click.echo(click.style(f"\t\t🔬 {test_name_padded} - {test}", fg="cyan"))
    else:
        click.echo(click.style("No tests found 😞", fg="red"))
