def test_streamlit_activate(self):
        process = subprocess.Popen(
            "streamlit activate", stdin=subprocess.PIPE, shell=True
        )
        process.stdin.write(b"regressiontest@streamlit.io\n")  # type: ignore
        process.stdin.flush()  # type: ignore
        process.communicate()

        with open(CREDENTIALS_FILE_PATH) as f:
            assert (
                "regressiontest@streamlit.io" in f.read()
            ), "Email address was not found in the credentials file"