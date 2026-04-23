def set_database_url(cls, value, info):
        if value and not is_valid_database_url(value):
            sanitized = sanitize_database_url(value)
            msg = f"Invalid database_url provided: '{sanitized}'"
            raise ValueError(msg)

        if langflow_database_url := os.getenv("LANGFLOW_DATABASE_URL"):
            value = langflow_database_url
            logger.debug("Using LANGFLOW_DATABASE_URL env variable")
        else:
            # Originally, we used sqlite:///./langflow.db
            # so we need to migrate to the new format
            # if there is a database in that location
            if not info.data["config_dir"]:
                msg = "config_dir not set, please set it or provide a database_url"
                raise ValueError(msg)

            from lfx.utils.version import get_version_info
            from lfx.utils.version import is_pre_release as langflow_is_pre_release

            version = get_version_info()["version"]
            is_pre_release = langflow_is_pre_release(version)

            if info.data["save_db_in_config_dir"]:
                database_dir = info.data["config_dir"]
            else:
                # Use langflow package path, not lfx, for backwards compatibility
                try:
                    import langflow

                    database_dir = Path(langflow.__file__).parent.resolve()
                except ImportError:
                    database_dir = Path(__file__).parent.parent.parent.resolve()

            pre_db_file_name = "langflow-pre.db"
            db_file_name = "langflow.db"
            new_pre_path = f"{database_dir}/{pre_db_file_name}"
            new_path = f"{database_dir}/{db_file_name}"
            final_path = None
            if is_pre_release:
                if Path(new_pre_path).exists():
                    final_path = new_pre_path
                elif Path(new_path).exists() and info.data["save_db_in_config_dir"]:
                    # We need to copy the current db to the new location
                    logger.debug("Copying existing database to new location")
                    copy2(new_path, new_pre_path)
                    logger.debug(f"Copied existing database to {new_pre_path}")
                elif Path(f"./{db_file_name}").exists() and info.data["save_db_in_config_dir"]:
                    logger.debug("Copying existing database to new location")
                    copy2(f"./{db_file_name}", new_pre_path)
                    logger.debug(f"Copied existing database to {new_pre_path}")
                else:
                    logger.debug(f"Creating new database at {new_pre_path}")
                    final_path = new_pre_path
            elif Path(new_path).exists():
                final_path = new_path
            elif Path(f"./{db_file_name}").exists():
                try:
                    logger.debug("Copying existing database to new location")
                    copy2(f"./{db_file_name}", new_path)
                    logger.debug(f"Copied existing database to {new_path}")
                except OSError:
                    logger.exception("Failed to copy database, using default path")
                    new_path = f"./{db_file_name}"
            else:
                final_path = new_path

            if final_path is None:
                final_path = new_pre_path if is_pre_release else new_path

            value = f"sqlite:///{final_path}"

        return value