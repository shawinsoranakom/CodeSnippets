def test_transcription():
    with (
        tempfile.NamedTemporaryFile("w") as input_file,
        tempfile.NamedTemporaryFile("r") as output_file,
    ):
        input_file.write(INPUT_TRANSCRIPTION_BATCH)
        input_file.flush()
        proc = subprocess.Popen(
            [
                "vllm",
                "run-batch",
                "-i",
                input_file.name,
                "-o",
                output_file.name,
                "--model",
                SPEECH_LARGE_MODEL_NAME,
            ],
        )
        proc.communicate()
        proc.wait()
        assert proc.returncode == 0, f"{proc=}"

        contents = output_file.read()
        print(f"\n\ncontents: {contents}\n\n")
        for line in contents.strip().split("\n"):
            BatchRequestOutput.model_validate_json(line)

            line_dict = json.loads(line)
            assert isinstance(line_dict, dict)
            assert line_dict["error"] is None

            response_body = line_dict["response"]["body"]
            assert response_body is not None
            assert "text" in response_body
            assert "usage" in response_body