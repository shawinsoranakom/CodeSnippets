def parse_fuller_format(lines: str | list[str]) -> GitCommit:
    """
    Expect commit message generated using `--format=fuller --date=unix` format, i.e.:
        commit <sha1>
        Author:     <author>
        AuthorDate: <author date>
        Commit:     <committer>
        CommitDate: <committer date>

        <title line>

        <full commit message>

    """
    if isinstance(lines, str):
        lines = lines.split("\n")
    # TODO: Handle merge commits correctly
    if len(lines) > 1 and lines[1].startswith("Merge:"):
        del lines[1]
    if len(lines) <= 7:
        raise AssertionError(
            f"Expected at least 8 lines in git log fuller format, got {len(lines)}"
        )
    if not lines[0].startswith("commit"):
        raise AssertionError(f"Expected line 0 to start with 'commit', got: {lines[0]}")
    if not lines[1].startswith("Author: "):
        raise AssertionError(
            f"Expected line 1 to start with 'Author: ', got: {lines[1]}"
        )
    if not lines[2].startswith("AuthorDate: "):
        raise AssertionError(
            f"Expected line 2 to start with 'AuthorDate: ', got: {lines[2]}"
        )
    if not lines[3].startswith("Commit: "):
        raise AssertionError(
            f"Expected line 3 to start with 'Commit: ', got: {lines[3]}"
        )
    if not lines[4].startswith("CommitDate: "):
        raise AssertionError(
            f"Expected line 4 to start with 'CommitDate: ', got: {lines[4]}"
        )
    if len(lines[5]) != 0:
        raise AssertionError(f"Expected line 5 to be empty, got: {lines[5]}")
    return GitCommit(
        commit_hash=lines[0].split()[1].strip(),
        author=lines[1].split(":", 1)[1].strip(),
        author_date=datetime.fromtimestamp(int(lines[2].split(":", 1)[1].strip())),
        commit_date=datetime.fromtimestamp(int(lines[4].split(":", 1)[1].strip())),
        title=lines[6].strip(),
        body="\n".join(lines[7:]),
    )