def get_available_extractors(cls,
                                 extractor_type: T.Literal["align", "detect", "identity", "mask"],
                                 add_none: bool = False,
                                 extend_plugin: bool = False) -> list[str]:
        """Return a list of available extractors of the given type

        Parameters
        ----------
        extractor_type
            The type of extractor to return the plugins for
        add_none
            Append "none" to the list of returned plugins. Default: False
        extend_plugin
            Some plugins have configuration options that mean that multiple 'pseudo-plugins'
            can be generated based on their settings. An example of this is the bisenet-fp mask
            which, whilst selected as 'bisenet-fp' can be stored as 'bisenet-fp-face' and
            'bisenet-fp-head' depending on whether hair has been included in the mask or not.
            ``True`` will generate each pseudo-plugin, ``False`` will generate the original
            plugin name. Default: ``False``

        Returns
        -------
        A list of the available extractor plugin names for the given type
        """
        if extractor_type not in cls.extract_plugins:
            raise ValueError(f"{extractor_type} is not a valid plugin type. Select from "
                             f"{list(cls.extract_plugins)}")
        plugins = [x.split(".")[-2].replace("_", "-") for x in cls.extract_plugins[extractor_type]]
        if extend_plugin and extractor_type == "mask":
            extendable = ["bisenet-fp", "custom"]
            for plugin in extendable:
                if plugin not in plugins:
                    continue
                plugins.remove(plugin)
                plugins.extend([f"{plugin}_face", f"{plugin}_head"])
        plugins = sorted(plugins)
        if add_none:
            plugins.insert(0, "none")
        return plugins