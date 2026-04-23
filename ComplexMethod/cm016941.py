def define_schema(cls):
        """
        For details about the supported file input types, see:
        https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference
        """
        input_dir = folder_paths.get_input_directory()
        input_files = [
            f
            for f in os.scandir(input_dir)
            if f.is_file()
            and (f.name.endswith(".txt") or f.name.endswith(".pdf"))
            and f.stat().st_size < GEMINI_MAX_INPUT_FILE_SIZE
        ]
        input_files = sorted(input_files, key=lambda x: x.name)
        input_files = [f.name for f in input_files]
        return IO.Schema(
            node_id="GeminiInputFiles",
            display_name="Gemini Input Files",
            category="api node/text/Gemini",
            description="Loads and prepares input files to include as inputs for Gemini LLM nodes. "
            "The files will be read by the Gemini model when generating a response. "
            "The contents of the text file count toward the token limit. "
            "🛈 TIP: Can be chained together with other Gemini Input File nodes.",
            inputs=[
                IO.Combo.Input(
                    "file",
                    options=input_files,
                    default=input_files[0] if input_files else None,
                    tooltip="Input files to include as context for the model. "
                    "Only accepts text (.txt) and PDF (.pdf) files for now.",
                ),
                IO.Custom("GEMINI_INPUT_FILES").Input(
                    "GEMINI_INPUT_FILES",
                    optional=True,
                    tooltip="An optional additional file(s) to batch together with the file loaded from this node. "
                    "Allows chaining of input files so that a single message can include multiple input files.",
                ),
            ],
            outputs=[
                IO.Custom("GEMINI_INPUT_FILES").Output(),
            ],
        )