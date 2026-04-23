def update_recent_files_list(self, new_file=None):
        "Load and update the recent files list and menus"
        # TODO: move to iomenu.
        rf_list = []
        file_path = self.recent_files_path
        if file_path and os.path.exists(file_path):
            with open(file_path,
                      encoding='utf_8', errors='replace') as rf_list_file:
                rf_list = rf_list_file.readlines()
        if new_file:
            new_file = os.path.abspath(new_file) + '\n'
            if new_file in rf_list:
                rf_list.remove(new_file)  # move to top
            rf_list.insert(0, new_file)
        # clean and save the recent files list
        bad_paths = []
        for path in rf_list:
            if '\0' in path or not os.path.exists(path[0:-1]):
                bad_paths.append(path)
        rf_list = [path for path in rf_list if path not in bad_paths]
        ulchars = "1234567890ABCDEFGHIJK"
        rf_list = rf_list[0:len(ulchars)]
        if file_path:
            try:
                with open(file_path, 'w',
                          encoding='utf_8', errors='replace') as rf_file:
                    rf_file.writelines(rf_list)
            except OSError as err:
                if not getattr(self.root, "recentfiles_message", False):
                    self.root.recentfiles_message = True
                    messagebox.showwarning(title='IDLE Warning',
                        message="Cannot save Recent Files list to disk.\n"
                                f"  {err}\n"
                                "Select OK to continue.",
                        parent=self.text)
        # for each edit window instance, construct the recent files menu
        for instance in self.top.instance_dict:
            menu = instance.recent_files_menu
            menu.delete(0, END)  # clear, and rebuild:
            for i, file_name in enumerate(rf_list):
                file_name = file_name.rstrip()  # zap \n
                callback = instance.__recent_file_callback(file_name)
                menu.add_command(label=ulchars[i] + " " + file_name,
                                 command=callback,
                                 underline=0)