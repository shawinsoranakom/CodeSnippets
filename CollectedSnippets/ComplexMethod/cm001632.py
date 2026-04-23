def load(self, filename):
        try:
            with open(filename, "r", encoding="utf8") as file:
                self.data = json.load(file)
        except FileNotFoundError:
            self.data = {}
        except Exception:
            errors.report(f'\nCould not load settings\nThe config file "{filename}" is likely corrupted\nIt has been moved to the "tmp/config.json"\nReverting config to default\n\n''', exc_info=True)
            os.replace(filename, os.path.join(script_path, "tmp", "config.json"))
            self.data = {}
        # 1.6.0 VAE defaults
        if self.data.get('sd_vae_as_default') is not None and self.data.get('sd_vae_overrides_per_model_preferences') is None:
            self.data['sd_vae_overrides_per_model_preferences'] = not self.data.get('sd_vae_as_default')

        # 1.1.1 quicksettings list migration
        if self.data.get('quicksettings') is not None and self.data.get('quicksettings_list') is None:
            self.data['quicksettings_list'] = [i.strip() for i in self.data.get('quicksettings').split(',')]

        # 1.4.0 ui_reorder
        if isinstance(self.data.get('ui_reorder'), str) and self.data.get('ui_reorder') and "ui_reorder_list" not in self.data:
            self.data['ui_reorder_list'] = [i.strip() for i in self.data.get('ui_reorder').split(',')]

        bad_settings = 0
        for k, v in self.data.items():
            info = self.data_labels.get(k, None)
            if info is not None and not self.same_type(info.default, v):
                print(f"Warning: bad setting value: {k}: {v} ({type(v).__name__}; expected {type(info.default).__name__})", file=sys.stderr)
                bad_settings += 1

        if bad_settings > 0:
            print(f"The program is likely to not work with bad settings.\nSettings file: {filename}\nEither fix the file, or delete it and restart.", file=sys.stderr)