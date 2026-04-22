def __init__(self, folder_blacklist):
        """Constructor.

        Parameters
        ----------
        folder_blacklist : list of str
            list of folder names with globbing to blacklist.

        """
        self._folder_blacklist = list(folder_blacklist)
        self._folder_blacklist.extend(DEFAULT_FOLDER_BLACKLIST)

        # Add the Streamlit lib folder when in dev mode, since otherwise we end
        # up with weird situations where the ID of a class in one run is not
        # the same as in another run.
        if config.get_option("global.developmentMode"):
            self._folder_blacklist.append(os.path.dirname(__file__))