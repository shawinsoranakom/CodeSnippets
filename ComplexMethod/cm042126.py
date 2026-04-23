async def test_git():
    local_path = Path(__file__).parent / "git"
    repo, subdir = await mock_repo(local_path)

    assert len(repo.changed_files) == 3
    repo.add_change(repo.changed_files)
    repo.commit("commit1")
    assert not repo.changed_files

    await mock_file(local_path / "a.txt", "tests")
    await mock_file(subdir / "d.txt")
    rmfile = local_path / "b.txt"
    rmfile.unlink()
    assert repo.status

    assert len(repo.changed_files) == 3
    repo.add_change(repo.changed_files)
    repo.commit("commit2")
    assert not repo.changed_files

    assert repo.status

    exist_dir = repo.workdir / "git4"
    exist_dir.mkdir(parents=True, exist_ok=True)
    repo.rename_root("git4")
    assert repo.workdir.name == "git4"

    repo.delete_repository()
    assert not local_path.exists()