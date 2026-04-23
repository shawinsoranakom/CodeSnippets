def _should_rerun_on_file_change(self, filepath: str) -> bool:
        main_script_path = self._session_data.main_script_path
        pages = source_util.get_pages(main_script_path)

        changed_page_script_hash = next(
            filter(lambda k: pages[k]["script_path"] == filepath, pages),
            None,
        )

        if changed_page_script_hash is not None:
            current_page_script_hash = self._client_state.page_script_hash
            return changed_page_script_hash == current_page_script_hash

        return True