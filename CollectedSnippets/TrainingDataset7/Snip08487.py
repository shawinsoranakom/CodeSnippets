def _ensure_location_group_id(self, full_path):
        if os.name == "posix":
            file_gid = os.stat(full_path).st_gid
            location_gid = os.stat(self.location).st_gid
            if file_gid != location_gid:
                try:
                    os.chown(full_path, uid=-1, gid=location_gid)
                except PermissionError:
                    pass