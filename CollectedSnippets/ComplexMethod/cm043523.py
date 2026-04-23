def load_prompt(
    input_repo: DiskMemory,
    improve_mode: bool,
    prompt_file: str,
    image_directory: str,
    entrypoint_prompt_file: str = "",
) -> Prompt:
    """
    Load or request a prompt from the user based on the mode.

    Parameters
    ----------
    input_repo : DiskMemory
        The disk memory object where prompts and other data are stored.
    improve_mode : bool
        Flag indicating whether the application is in improve mode.

    Returns
    -------
    str
        The loaded or inputted prompt.
    """

    if os.path.isdir(prompt_file):
        raise ValueError(
            f"The path to the prompt, {prompt_file}, already exists as a directory. No prompt can be read from it. Please specify a prompt file using --prompt_file"
        )
    prompt_str = input_repo.get(prompt_file)
    if prompt_str:
        print(colored("Using prompt from file:", "green"), prompt_file)
        print(prompt_str)
    else:
        if not improve_mode:
            prompt_str = input(
                "\nWhat application do you want gpt-engineer to generate?\n"
            )
        else:
            prompt_str = input("\nHow do you want to improve the application?\n")

    if entrypoint_prompt_file == "":
        entrypoint_prompt = ""
    else:
        full_entrypoint_prompt_file = concatenate_paths(
            input_repo.path, entrypoint_prompt_file
        )
        if os.path.isfile(full_entrypoint_prompt_file):
            entrypoint_prompt = input_repo.get(full_entrypoint_prompt_file)

        else:
            raise ValueError("The provided file at --entrypoint-prompt does not exist")

    if image_directory == "":
        return Prompt(prompt_str, entrypoint_prompt=entrypoint_prompt)

    full_image_directory = concatenate_paths(input_repo.path, image_directory)
    if os.path.isdir(full_image_directory):
        if len(os.listdir(full_image_directory)) == 0:
            raise ValueError("The provided --image_directory is empty.")
        image_repo = DiskMemory(full_image_directory)
        return Prompt(
            prompt_str,
            image_repo.get(".").to_dict(),
            entrypoint_prompt=entrypoint_prompt,
        )
    else:
        raise ValueError("The provided --image_directory is not a directory.")