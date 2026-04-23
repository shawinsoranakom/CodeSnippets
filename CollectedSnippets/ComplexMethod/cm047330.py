def _get_paths(self, path_def, installed):
        """
        Returns a list of tuple (path, full_path, modified) matching a given glob (path_def).
        The glob can only occur in the static direcory of an installed addon.

        If the path_def matches a (list of) file, the result will contain the full_path
        and the modified time.
        Ex: ('/base/static/file.js', '/home/user/source/odoo/odoo/addons/base/static/file.js', 643636800)

        If the path_def looks like a non aggregable path (http://, /web/assets), only return the path
        Ex: ('http://example.com/lib.js', None, -1)
        The timestamp -1 is given to be thruthy while carrying no information.

        If the path_def is not a wildward, but may still be a valid addons path, return a False path
        with No timetamp
        Ex: ('/_custom/web.asset_frontend', False, None)

        :param path_def: the definition (glob) of file paths to match
        :param installed: the list of installed addons
        :returns: a list of tuple: (path, full_path, modified)
        """
        paths = None
        path_def = fs2web(path_def)  # we expect to have all path definition unix style or url style, this is a safety
        path_parts = [part for part in path_def.split('/') if part]
        addon = path_parts[0]
        addon_manifest = Manifest.for_addon(addon, display_warning=False)

        safe_path = False
        if addon_manifest:
            if addon not in installed:
                # Assert that the path is in the installed addons
                raise Exception(f"""Unallowed to fetch files from addon {addon} for file {path_def}. """
                                f"""Addon {addon} is not installed""")
            addons_path = addon_manifest.addons_path
            full_path = os.path.normpath(os.path.join(addons_path, *path_parts))
            # forbid escape from the current addon
            # "/mymodule/../myothermodule" is forbidden
            static_prefix = os.path.join(addon_manifest.path, 'static', '')
            if full_path.startswith(static_prefix):
                paths_with_timestamps = _glob_static_file(full_path)
                paths = [
                    (fs2web(absolute_path[len(addons_path):]), absolute_path, timestamp)
                    for absolute_path, timestamp in paths_with_timestamps
                ]
                safe_path = True

        if not paths and not can_aggregate(path_def):  # http:// or /web/content
            paths = [(path_def, EXTERNAL_ASSET, -1)]

        if not paths and not is_wildcard_glob(path_def):  # an attachment url most likely
            paths = [(path_def, None, None)]

        if not paths:
            msg = f'IrAsset: the path "{path_def}" did not resolve to anything.'
            if not safe_path:
                msg += " It may be due to security reasons."
            _logger.warning(msg)
        # Paths are filtered on the extensions (if any).
        return paths