def _get_paths_with_context(self, subdirs=True):
        """ Return a list of PluginPathContext objects to search for plugins in """

        # FIXME: This is potentially buggy if subdirs is sometimes True and sometimes False.
        # In current usage, everything calls this with subdirs=True except for module_utils_loader and ansible-doc
        # which always calls it with subdirs=False. So there currently isn't a problem with this caching.
        if self._paths is not None:
            return self._paths

        ret = [PluginPathContext(p, False) for p in self._extra_dirs]

        # look in any configured plugin paths, allow one level deep for subcategories
        if self.config is not None:
            for path in self.config:
                path = os.path.abspath(os.path.expanduser(path))
                if subdirs:
                    contents = glob.glob("%s/*" % path) + glob.glob("%s/*/*" % path)
                    for c in contents:
                        c = to_text(c, errors='surrogate_or_strict')
                        if os.path.isdir(c) and c not in ret:
                            ret.append(PluginPathContext(c, False))

                path = to_text(path, errors='surrogate_or_strict')
                if path not in ret:
                    ret.append(PluginPathContext(path, False))

        # look for any plugins installed in the package subtree
        # Note package path always gets added last so that every other type of
        # path is searched before it.
        ret.extend([PluginPathContext(p, True) for p in self._get_package_paths(subdirs=subdirs)])

        # HACK: because powershell modules are in the same directory
        # hierarchy as other modules we have to process them last.  This is
        # because powershell only works on windows but the other modules work
        # anywhere (possibly including windows if the correct language
        # interpreter is installed).  the non-powershell modules can have any
        # file extension and thus powershell modules are picked up in that.
        # The non-hack way to fix this is to have powershell modules be
        # a different PluginLoader/ModuleLoader.  But that requires changing
        # other things too (known thing to change would be PATHS_CACHE,
        # PLUGIN_PATHS_CACHE, and MODULE_CACHE.  Since those three dicts key
        # on the class_name and neither regular modules nor powershell modules
        # would have class_names, they would not work as written.
        #
        # The expected sort order is paths in the order in 'ret' with paths ending in '/windows' at the end,
        # also in the original order they were found in 'ret'.
        # The .sort() method is guaranteed to be stable, so original order is preserved.
        ret.sort(key=lambda p: p.path.endswith('/windows'))

        # cache and return the result
        self._paths = ret
        return ret