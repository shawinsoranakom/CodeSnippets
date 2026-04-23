def git_branch(
        self,
        repo_path: str | None = None,
        name: str | None = None,
        delete: bool = False,
    ) -> str:
        """List, create, or delete branches.

        Args:
            repo_path: Path to the repository
            name: Branch name to create/delete
            delete: Whether to delete the branch

        Returns:
            str: Result of the operation
        """
        repo = self._get_repo(repo_path)

        try:
            if name is None:
                # List branches
                branches = []
                current = repo.active_branch.name if not repo.head.is_detached else None
                for branch in repo.branches:
                    prefix = "* " if branch.name == current else "  "
                    branches.append(f"{prefix}{branch.name}")
                return "\n".join(branches) if branches else "No branches found"

            if delete:
                # Delete branch
                repo.delete_head(name, force=True)
                return f"Deleted branch '{name}'"
            else:
                # Create branch
                repo.create_head(name)
                return f"Created branch '{name}'"

        except GitCommandError as e:
            raise CommandExecutionError(f"Branch operation failed: {e}")