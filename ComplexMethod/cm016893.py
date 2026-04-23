def get_request_user_filepath(self, request, file, type="userdata", create_dir=True):
        if type == "userdata":
            root_dir = folder_paths.get_user_directory()
        else:
            raise KeyError("Unknown filepath type:" + type)

        user = self.get_request_user_id(request)
        user_root = folder_paths.get_public_user_directory(user)
        if user_root is None:
            return None
        path = user_root

        # prevent leaving /{type}
        if os.path.commonpath((root_dir, user_root)) != root_dir:
            return None

        if file is not None:
            # Check if filename is url encoded
            if "%" in file:
                file = parse.unquote(file)

            # prevent leaving /{type}/{user}
            path = os.path.abspath(os.path.join(user_root, file))
            if os.path.commonpath((user_root, path)) != user_root:
                return None

        parent = os.path.split(path)[0]

        if create_dir and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        return path