def download_button(
        self,
        label: str,
        data: DownloadButtonDataType,
        file_name: Optional[str] = None,
        mime: Optional[str] = None,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_click: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
    ) -> bool:
        """Display a download button widget.

        This is useful when you would like to provide a way for your users
        to download a file directly from your app.

        Note that the data to be downloaded is stored in-memory while the
        user is connected, so it's a good idea to keep file sizes under a
        couple hundred megabytes to conserve memory.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this button is for.
            The label can optionally contain Markdown and supports the following
            elements: Bold, Italics, Strikethroughs, and Emojis.
        data : str or bytes or file
            The contents of the file to be downloaded. See example below for
            caching techniques to avoid recomputing this data unnecessarily.
        file_name: str
            An optional string to use as the name of the file to be downloaded,
            such as 'my_file.csv'. If not specified, the name will be
            automatically generated.
        mime : str or None
            The MIME type of the data. If None, defaults to "text/plain"
            (if data is of type *str* or is a textual *file*) or
            "application/octet-stream" (if data is of type *bytes* or is a
            binary *file*).
        key : str or int
            An optional string or integer to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        help : str
            An optional tooltip that gets displayed when the button is
            hovered over.
        on_click : callable
            An optional callback invoked when this button is clicked.
        args : tuple
            An optional tuple of args to pass to the callback.
        kwargs : dict
            An optional dict of kwargs to pass to the callback.
        disabled : bool
            An optional boolean, which disables the download button if set to
            True. The default is False. This argument can only be supplied by
            keyword.

        Returns
        -------
        bool
            True if the button was clicked on the last run of the app,
            False otherwise.

        Examples
        --------
        Download a large DataFrame as a CSV:

        >>> @st.cache
        ... def convert_df(df):
        ...     # IMPORTANT: Cache the conversion to prevent computation on every rerun
        ...     return df.to_csv().encode('utf-8')
        >>>
        >>> csv = convert_df(my_large_df)
        >>>
        >>> st.download_button(
        ...     label="Download data as CSV",
        ...     data=csv,
        ...     file_name='large_df.csv',
        ...     mime='text/csv',
        ... )

        Download a string as a file:

        >>> text_contents = '''This is some text'''
        >>> st.download_button('Download some text', text_contents)

        Download a binary file:

        >>> binary_contents = b'example content'
        >>> # Defaults to 'application/octet-stream'
        >>> st.download_button('Download binary file', binary_contents)

        Download an image:

        >>> with open("flower.png", "rb") as file:
        ...     btn = st.download_button(
        ...             label="Download image",
        ...             data=file,
        ...             file_name="flower.png",
        ...             mime="image/png"
        ...           )

        .. output::
           https://doc-download-buton.streamlitapp.com/
           height: 335px

        """
        ctx = get_script_run_ctx()
        return self._download_button(
            label=label,
            data=data,
            file_name=file_name,
            mime=mime,
            key=key,
            help=help,
            on_click=on_click,
            args=args,
            kwargs=kwargs,
            disabled=disabled,
            ctx=ctx,
        )