def git_status(self, repo_path: str | None = None) -> str:
        """Show the working tree status.

        Args:
            repo_path: Path to the repository

        Returns:
            str: Status information
        """
        repo = self._get_repo(repo_path)

        # Get the current branch
        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = "HEAD detached"

        # Get status information
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        unstaged = [item.a_path for item in repo.index.diff(None)]
        untracked = repo.untracked_files

        lines = [f"On branch {branch}", ""]

        if staged:
            lines.append("Changes to be committed:")
            for file in staged:
                lines.append(f"  modified: {file}")
            lines.append("")

        if unstaged:
            lines.append("Changes not staged for commit:")
            for file in unstaged:
                lines.append(f"  modified: {file}")
            lines.append("")

        if untracked:
            lines.append("Untracked files:")
            for file in untracked:
                lines.append(f"  {file}")
            lines.append("")

        if not staged and not unstaged and not untracked:
            lines.append("nothing to commit, working tree clean")

        return "\n".join(lines)