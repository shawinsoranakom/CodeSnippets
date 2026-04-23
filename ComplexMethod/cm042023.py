async def mermaid_to_file(
    engine,
    mermaid_code,
    output_file_without_suffix,
    width=2048,
    height=2048,
    config=None,
    suffixes: Optional[List[str]] = None,
) -> int:
    """Convert Mermaid code to various file formats.

    Args:
        engine (str): The engine to use for conversion. Supported engines are "nodejs", "playwright", "pyppeteer", "ink", and "none".
        mermaid_code (str): The Mermaid code to be converted.
        output_file_without_suffix (str): The output file name without the suffix.
        width (int, optional): The width of the output image. Defaults to 2048.
        height (int, optional): The height of the output image. Defaults to 2048.
        config (Optional[Config], optional): The configuration to use for the conversion. Defaults to None, which uses the default configuration.
        suffixes (Optional[List[str]], optional): The file suffixes to generate. Supports "png", "pdf", and "svg". Defaults to ["png"].

    Returns:
        int: 0 if the conversion is successful, -1 if the conversion fails.
    """
    file_head = "%%{init: {'theme': 'default', 'themeVariables': { 'fontFamily': 'Inter' }}}%%\n"
    if not re.match(r"^%%\{.+", mermaid_code):
        mermaid_code = file_head + mermaid_code
    suffixes = suffixes or ["svg"]
    # Write the Mermaid code to a temporary file
    config = config if config else Config.default()
    dir_name = os.path.dirname(output_file_without_suffix)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    tmp = Path(f"{output_file_without_suffix}.mmd")
    await awrite(filename=tmp, data=mermaid_code)

    if engine == "nodejs":
        if check_cmd_exists(config.mermaid.path) != 0:
            logger.warning(
                "RUN `npm install -g @mermaid-js/mermaid-cli` to install mmdc,"
                "or consider changing engine to `playwright`, `pyppeteer`, or `ink`."
            )
            return -1

        for suffix in suffixes:
            output_file = f"{output_file_without_suffix}.{suffix}"
            # Call the `mmdc` command to convert the Mermaid code to a PNG
            logger.info(f"Generating {output_file}..")

            if config.mermaid.puppeteer_config:
                commands = [
                    config.mermaid.path,
                    "-p",
                    config.mermaid.puppeteer_config,
                    "-i",
                    str(tmp),
                    "-o",
                    output_file,
                    "-w",
                    str(width),
                    "-H",
                    str(height),
                ]
            else:
                commands = [config.mermaid.path, "-i", str(tmp), "-o", output_file, "-w", str(width), "-H", str(height)]
            process = await asyncio.create_subprocess_shell(
                " ".join(commands), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            if stdout:
                logger.info(stdout.decode())
            if stderr:
                logger.warning(stderr.decode())
    else:
        if engine == "playwright":
            from metagpt.utils.mmdc_playwright import mermaid_to_file

            return await mermaid_to_file(mermaid_code, output_file_without_suffix, width, height, suffixes=suffixes)
        elif engine == "pyppeteer":
            from metagpt.utils.mmdc_pyppeteer import mermaid_to_file

            return await mermaid_to_file(mermaid_code, output_file_without_suffix, width, height, suffixes=suffixes)
        elif engine == "ink":
            from metagpt.utils.mmdc_ink import mermaid_to_file

            return await mermaid_to_file(mermaid_code, output_file_without_suffix, suffixes=suffixes)
        elif engine == "none":
            return 0
        else:
            logger.warning(f"Unsupported mermaid engine: {engine}")
    return 0