def _handle_git_information_request(self) -> None:
        msg = ForwardMsg()

        try:
            from streamlit.git_util import GitRepo

            repo = GitRepo(self._session_data.main_script_path)

            repo_info = repo.get_repo_info()
            if repo_info is None:
                return

            repository_name, branch, module = repo_info

            msg.git_info_changed.repository = repository_name
            msg.git_info_changed.branch = branch
            msg.git_info_changed.module = module

            msg.git_info_changed.untracked_files[:] = repo.untracked_files
            msg.git_info_changed.uncommitted_files[:] = repo.uncommitted_files

            if repo.is_head_detached:
                msg.git_info_changed.state = GitInfo.GitStates.HEAD_DETACHED
            elif len(repo.ahead_commits) > 0:
                msg.git_info_changed.state = GitInfo.GitStates.AHEAD_OF_REMOTE
            else:
                msg.git_info_changed.state = GitInfo.GitStates.DEFAULT

            self._enqueue_forward_msg(msg)
        except Exception as ex:
            # Users may never even install Git in the first place, so this
            # error requires no action. It can be useful for debugging.
            LOGGER.debug("Obtaining Git information produced an error", exc_info=ex)