async def generate_release_notes(repo_path: Optional[str | Path] = None):
    logger = logging.getLogger(generate_release_notes.name)  # pyright: ignore

    repo = Repo(repo_path, search_parent_directories=True)
    tags = list(repo.tags)
    if not tags:
        click.echo("No tags found in the repository.")
        return

    click.echo("Available tags:")
    for index, tag in enumerate(tags):
        click.echo(f"{index + 1}: {tag.name}")

    last_release_index = (
        click.prompt("Enter the number for the last release tag", type=int) - 1
    )
    if last_release_index >= len(tags) or last_release_index < 0:
        click.echo("Invalid tag number entered.")
        return
    last_release_tag: TagReference = tags[last_release_index]

    new_release_ref = click.prompt(
        "Enter the name of the release branch or git ref",
        default=repo.active_branch.name,
    )
    try:
        new_release_ref = repo.heads[new_release_ref].name
    except IndexError:
        try:
            new_release_ref = repo.tags[new_release_ref].name
        except IndexError:
            new_release_ref = repo.commit(new_release_ref).hexsha
    logger.debug(f"Selected release ref: {new_release_ref}")

    git_log = repo.git.log(
        f"{last_release_tag.name}...{new_release_ref}",
        "classic/original_autogpt/",
        no_merges=True,
        follow=True,
    )
    logger.debug(f"-------------- GIT LOG --------------\n\n{git_log}\n")

    model_provider = MultiProvider()
    chat_messages = [
        ChatMessage.system(SYSTEM_PROMPT),
        ChatMessage.user(content=git_log),
    ]
    click.echo("Writing release notes ...")
    completion = await model_provider.create_chat_completion(
        model_prompt=chat_messages,
        model_name=AnthropicModelName.CLAUDE3_OPUS_v1,
        # model_name=OpenAIModelName.GPT4_v4,
    )

    click.echo("-------------- LLM RESPONSE --------------\n")
    click.echo(completion.response.content)
