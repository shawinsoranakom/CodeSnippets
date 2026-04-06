def list_outdated(language: str) -> list[Path]:
    dir_path = Path(__file__).absolute().parent.parent
    repo = git.Repo(dir_path)

    outdated_paths: list[Path] = []
    en_lang_paths = list(iter_en_paths_to_translate())
    for path in en_lang_paths:
        lang_path = generate_lang_path(lang=language, path=path)
        if not lang_path.exists():
            continue
        en_commit_datetime = list(repo.iter_commits(paths=path, max_count=1))[
            0
        ].committed_datetime
        lang_commit_datetime = list(repo.iter_commits(paths=lang_path, max_count=1))[
            0
        ].committed_datetime
        if lang_commit_datetime < en_commit_datetime:
            outdated_paths.append(path)
    print(outdated_paths)
    return outdated_paths