async def refresh_repo(instance, test_repo_dir, reclone_existing_repo=False):
    terminal = Terminal()
    try:
        repo_path = Path(test_repo_dir) / (
            instance["repo"].replace("-", "_").replace("/", "__") + "_" + instance["version"]
        )
        repo_identifier = instance["repo"]
        base_commit = instance["base_commit"]
        if os.path.exists(repo_path) and reclone_existing_repo is True:
            logger.info(f"remove exist repo path:{repo_path.absolute()}")
            shutil.rmtree(repo_path)
        if os.path.exists(repo_path):
            logger.info(f"reset exist repo path:{repo_path.absolute()}")
            for cmd in [
                f"cd {repo_path.absolute()}",
                "git reset --hard && git clean -n -d && git clean -f -d",
                "BRANCH=$(git remote show origin | awk '/HEAD branch/ {print $NF}')",
                'git checkout "$BRANCH"',
                "git branch",
                "pwd",
            ]:
                await terminal_run_command(cmd, terminal)
        else:
            logger.info(f"clone repo to path:{repo_path}")
            for cmd in [
                f"git clone 'https://github.com/{repo_identifier}.git' {repo_path.absolute()}",
                f"cd {repo_path.absolute()}" + f" && git checkout -f {base_commit}" if base_commit else "",
                "git branch",
                "pwd",
            ]:
                await terminal_run_command(cmd, terminal)
    except Exception as e:
        logger.warning(e)
    finally:
        await terminal.close()
    return repo_path