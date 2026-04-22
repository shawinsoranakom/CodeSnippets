def main():
    # First run the 'streamlit commands'
    run_commands("Basic Commands", ["streamlit version"])

    run_commands(
        "Standard System Errors",
        ["streamlit run does_not_exist.py"],
        comment="Checks to see that file not found error is caught",
    )

    run_commands("Hello script", ["streamlit hello"])

    run_commands(
        "Examples",
        [
            "streamlit run %(EXAMPLE_DIR)s/%(filename)s"
            % {"EXAMPLE_DIR": EXAMPLE_DIR, "filename": filename}
            for filename in os.listdir(EXAMPLE_DIR)
            if filename.endswith(".py") and filename not in EXCLUDED_FILENAMES
        ],
    )

    run_commands(
        "Caching",
        ["streamlit cache clear", "streamlit run %s/caching.py" % EXAMPLE_DIR],
    )

    run_commands(
        "MNIST", ["streamlit run %s/mnist-cnn.py" % EXAMPLE_DIR], skip_last_input=True
    )

    click.secho("\n\nCompleted all tests!", bold=True)