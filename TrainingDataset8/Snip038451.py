def is_running_hello(self) -> bool:
        from streamlit.hello import Hello

        return self._main_script_path == Hello.__file__