def _get_delta_path_str(self) -> str:
        """Returns the element's delta path as a string like "[0, 2, 3, 1]".

        This uniquely identifies the element's position in the front-end,
        which allows (among other potential uses) the MediaFileManager to maintain
        session-specific maps of MediaFile objects placed with their "coordinates".

        This way, users can (say) use st.image with a stream of different images,
        and Streamlit will expire the older images and replace them in place.
        """
        # Operate on the active DeltaGenerator, in case we're in a `with` block.
        dg = self._active_dg
        return str(dg._cursor.delta_path) if dg._cursor is not None else "[]"