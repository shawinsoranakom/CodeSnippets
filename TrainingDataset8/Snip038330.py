def __init__(self, main_script_path: str):
        self._main_script_path = os.path.abspath(main_script_path)
        self._script_folder = os.path.dirname(self._main_script_path)
        self._on_file_changed: List[Callable[[str], None]] = []
        self._is_closed = False
        self._cached_sys_modules: Set[str] = set()

        # Blacklist for folders that should not be watched
        self._folder_black_list = FolderBlackList(
            config.get_option("server.folderWatchBlacklist")
        )

        self._watched_modules: Dict[str, WatchedModule] = {}

        for page_info in get_pages(self._main_script_path).values():
            self._register_watcher(
                page_info["script_path"],
                module_name=None,  # Only root scripts have their modules set to None
            )