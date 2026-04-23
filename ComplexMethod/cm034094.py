def __init__(
        self,
        include_lsb: Optional[bool] = None,
        os_release_file: str = "",
        distro_release_file: str = "",
        include_uname: Optional[bool] = None,
        root_dir: Optional[str] = None,
        include_oslevel: Optional[bool] = None,
    ) -> None:
        """
        The initialization method of this class gathers information from the
        available data sources, and stores that in private instance attributes.
        Subsequent access to the information items uses these private instance
        attributes, so that the data sources are read only once.

        Parameters:

        * ``include_lsb`` (bool): Controls whether the
          `lsb_release command output`_ is included as a data source.

          If the lsb_release command is not available in the program execution
          path, the data source for the lsb_release command will be empty.

        * ``os_release_file`` (string): The path name of the
          `os-release file`_ that is to be used as a data source.

          An empty string (the default) will cause the default path name to
          be used (see `os-release file`_ for details).

          If the specified or defaulted os-release file does not exist, the
          data source for the os-release file will be empty.

        * ``distro_release_file`` (string): The path name of the
          `distro release file`_ that is to be used as a data source.

          An empty string (the default) will cause a default search algorithm
          to be used (see `distro release file`_ for details).

          If the specified distro release file does not exist, or if no default
          distro release file can be found, the data source for the distro
          release file will be empty.

        * ``include_uname`` (bool): Controls whether uname command output is
          included as a data source. If the uname command is not available in
          the program execution path the data source for the uname command will
          be empty.

        * ``root_dir`` (string): The absolute path to the root directory to use
          to find distro-related information files. Note that ``include_*``
          parameters must not be enabled in combination with ``root_dir``.

        * ``include_oslevel`` (bool): Controls whether (AIX) oslevel command
          output is included as a data source. If the oslevel command is not
          available in the program execution path the data source will be
          empty.

        Public instance attributes:

        * ``os_release_file`` (string): The path name of the
          `os-release file`_ that is actually used as a data source. The
          empty string if no distro release file is used as a data source.

        * ``distro_release_file`` (string): The path name of the
          `distro release file`_ that is actually used as a data source. The
          empty string if no distro release file is used as a data source.

        * ``include_lsb`` (bool): The result of the ``include_lsb`` parameter.
          This controls whether the lsb information will be loaded.

        * ``include_uname`` (bool): The result of the ``include_uname``
          parameter. This controls whether the uname information will
          be loaded.

        * ``include_oslevel`` (bool): The result of the ``include_oslevel``
          parameter. This controls whether (AIX) oslevel information will be
          loaded.

        * ``root_dir`` (string): The result of the ``root_dir`` parameter.
          The absolute path to the root directory to use to find distro-related
          information files.

        Raises:

        * :py:exc:`ValueError`: Initialization parameters combination is not
           supported.

        * :py:exc:`OSError`: Some I/O issue with an os-release file or distro
          release file.

        * :py:exc:`UnicodeError`: A data source has unexpected characters or
          uses an unexpected encoding.
        """
        self.root_dir = root_dir
        self.etc_dir = os.path.join(root_dir, "etc") if root_dir else _UNIXCONFDIR
        self.usr_lib_dir = (
            os.path.join(root_dir, "usr/lib") if root_dir else _UNIXUSRLIBDIR
        )

        if os_release_file:
            self.os_release_file = os_release_file
        else:
            etc_dir_os_release_file = os.path.join(self.etc_dir, _OS_RELEASE_BASENAME)
            usr_lib_os_release_file = os.path.join(
                self.usr_lib_dir, _OS_RELEASE_BASENAME
            )

            # NOTE: The idea is to respect order **and** have it set
            #       at all times for API backwards compatibility.
            if os.path.isfile(etc_dir_os_release_file) or not os.path.isfile(
                usr_lib_os_release_file
            ):
                self.os_release_file = etc_dir_os_release_file
            else:
                self.os_release_file = usr_lib_os_release_file

        self.distro_release_file = distro_release_file or ""  # updated later

        is_root_dir_defined = root_dir is not None
        if is_root_dir_defined and (include_lsb or include_uname or include_oslevel):
            raise ValueError(
                "Including subprocess data sources from specific root_dir is disallowed"
                " to prevent false information"
            )
        self.include_lsb = (
            include_lsb if include_lsb is not None else not is_root_dir_defined
        )
        self.include_uname = (
            include_uname if include_uname is not None else not is_root_dir_defined
        )
        self.include_oslevel = (
            include_oslevel if include_oslevel is not None else not is_root_dir_defined
        )