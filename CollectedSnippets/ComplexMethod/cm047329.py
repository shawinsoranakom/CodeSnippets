def _process_path(self, bundle, directive, target, path_def, asset_paths, seen, addons, installed, bundle_start_index, **assets_params):
        """
        This sub function is meant to take a directive and a set of
        arguments and apply them to the current asset_paths list
        accordingly.

        It is nested inside `_get_asset_paths` since we need the current
        list of addons, extensions and asset_paths.

        :param directive: string
        :param target: string or None or False
        :param path_def: string
        """
        if directive == INCLUDE_DIRECTIVE:
            # recursively call this function for each INCLUDE_DIRECTIVE directive.
            self._fill_asset_paths(path_def, asset_paths, seen + [bundle], addons, installed, **assets_params)
            return
        if can_aggregate(path_def):
            paths = self._get_paths(path_def, installed)
        else:
            paths = [(path_def, EXTERNAL_ASSET, -1)]  # external urls

        # retrieve target index when it applies
        if directive in DIRECTIVES_WITH_TARGET:
            target_paths = self._get_paths(target, installed)
            if not target_paths and target.rpartition('.')[2] not in ASSET_EXTENSIONS:
                # nothing to do: the extension of the target is wrong
                return
            if target_paths:
                target = target_paths[0][0]
            target_index = asset_paths.index(target, bundle)

        if directive == APPEND_DIRECTIVE:
            asset_paths.append(paths, bundle)
        elif directive == PREPEND_DIRECTIVE:
            asset_paths.insert(paths, bundle, bundle_start_index)
        elif directive == AFTER_DIRECTIVE:
            asset_paths.insert(paths, bundle, target_index + 1)
        elif directive == BEFORE_DIRECTIVE:
            asset_paths.insert(paths, bundle, target_index)
        elif directive == REMOVE_DIRECTIVE:
            asset_paths.remove(paths, bundle)
        elif directive == REPLACE_DIRECTIVE:
            asset_paths.insert(paths, bundle, target_index)
            asset_paths.remove(target_paths, bundle)
        else:
            # this should never happen
            raise ValueError("Unexpected directive")