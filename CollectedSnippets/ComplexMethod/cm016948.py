def define_schema(cls):
        """
        For details about the supported file input types, see:
        https://platform.openai.com/docs/guides/pdf-files?api-mode=responses
        """
        input_dir = folder_paths.get_input_directory()
        input_files = [
            f
            for f in os.scandir(input_dir)
            if f.is_file()
            and (f.name.endswith(".txt") or f.name.endswith(".pdf"))
            and f.stat().st_size < 32 * 1024 * 1024
        ]
        input_files = sorted(input_files, key=lambda x: x.name)
        input_files = [f.name for f in input_files]
        return IO.Schema(
            node_id="OpenAIInputFiles",
            display_name="OpenAI ChatGPT Input Files",
            category="api node/text/OpenAI",
            description="Loads and prepares input files (text, pdf, etc.) to include as inputs for the OpenAI Chat Node. The files will be read by the OpenAI model when generating a response. 🛈 TIP: Can be chained together with other OpenAI Input File nodes.",
            inputs=[
                IO.Combo.Input(
                    "file",
                    options=input_files,
                    default=input_files[0] if input_files else None,
                    tooltip="Input files to include as context for the model. Only accepts text (.txt) and PDF (.pdf) files for now.",
                ),
                IO.Custom("OPENAI_INPUT_FILES").Input(
                    "OPENAI_INPUT_FILES",
                    tooltip="An optional additional file(s) to batch together with the file loaded from this node. Allows chaining of input files so that a single message can include multiple input files.",
                    optional=True,
                ),
            ],
            outputs=[
                IO.Custom("OPENAI_INPUT_FILES").Output(),
            ],
        )