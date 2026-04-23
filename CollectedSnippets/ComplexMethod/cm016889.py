def build_translations(self):
        """Load all custom nodes translations during initialization. Translations are
        expected to be loaded from `locales/` folder.

        The folder structure is expected to be the following:
        - custom_nodes/
            - custom_node_1/
                - locales/
                    - en/
                        - main.json
                        - commands.json
                        - settings.json

        returned translations are expected to be in the following format:
        {
            "en": {
                "nodeDefs": {...},
                "commands": {...},
                "settings": {...},
                ...{other main.json keys}
            }
        }
        """

        translations = {}

        for folder in folder_paths.get_folder_paths("custom_nodes"):
            # Sort glob results for deterministic ordering
            for custom_node_dir in sorted(glob.glob(os.path.join(folder, "*/"))):
                locales_dir = os.path.join(custom_node_dir, "locales")
                if not os.path.exists(locales_dir):
                    continue

                for lang_dir in glob.glob(os.path.join(locales_dir, "*/")):
                    lang_code = os.path.basename(os.path.dirname(lang_dir))

                    if lang_code not in translations:
                        translations[lang_code] = {}

                    # Load main.json
                    main_file = os.path.join(lang_dir, "main.json")
                    node_translations = safe_load_json_file(main_file)

                    # Load extra locale files
                    for extra_file in EXTRA_LOCALE_FILES:
                        extra_file_path = os.path.join(lang_dir, extra_file)
                        key = extra_file.split(".")[0]
                        json_data = safe_load_json_file(extra_file_path)
                        if json_data:
                            node_translations[key] = json_data

                    if node_translations:
                        translations[lang_code] = merge_json_recursive(
                            translations[lang_code], node_translations
                        )

        return translations