def form(self, key: str, clear_on_submit: bool = False):
        """Create a form that batches elements together with a "Submit" button.

        A form is a container that visually groups other elements and
        widgets together, and contains a Submit button. When the form's
        Submit button is pressed, all widget values inside the form will be
        sent to Streamlit in a batch.

        To add elements to a form object, you can use "with" notation
        (preferred) or just call methods directly on the form. See
        examples below.

        Forms have a few constraints:

        * Every form must contain a ``st.form_submit_button``.
        * ``st.button`` and ``st.download_button`` cannot be added to a form.
        * Forms can appear anywhere in your app (sidebar, columns, etc),
          but they cannot be embedded inside other forms.

        For more information about forms, check out our
        `blog post <https://blog.streamlit.io/introducing-submit-button-and-forms/>`_.

        Parameters
        ----------
        key : str
            A string that identifies the form. Each form must have its own
            key. (This key is not displayed to the user in the interface.)
        clear_on_submit : bool
            If True, all widgets inside the form will be reset to their default
            values after the user presses the Submit button. Defaults to False.
            (Note that Custom Components are unaffected by this flag, and
            will not be reset to their defaults on form submission.)

        Examples
        --------

        Inserting elements using "with" notation:

        >>> with st.form("my_form"):
        ...    st.write("Inside the form")
        ...    slider_val = st.slider("Form slider")
        ...    checkbox_val = st.checkbox("Form checkbox")
        ...
        ...    # Every form must have a submit button.
        ...    submitted = st.form_submit_button("Submit")
        ...    if submitted:
        ...        st.write("slider", slider_val, "checkbox", checkbox_val)
        ...
        >>> st.write("Outside the form")

        Inserting elements out of order:

        >>> form = st.form("my_form")
        >>> form.slider("Inside the form")
        >>> st.slider("Outside the form")
        >>>
        >>> # Now add a submit button to the form:
        >>> form.form_submit_button("Submit")

        """
        # Import this here to avoid circular imports.
        from streamlit.elements.utils import check_session_state_rules

        if is_in_form(self.dg):
            raise StreamlitAPIException("Forms cannot be nested in other forms.")

        check_session_state_rules(default_value=None, key=key, writes_allowed=False)

        # A form is uniquely identified by its key.
        form_id = key

        ctx = get_script_run_ctx()
        if ctx is not None:
            new_form_id = form_id not in ctx.form_ids_this_run
            if new_form_id:
                ctx.form_ids_this_run.add(form_id)
            else:
                raise StreamlitAPIException(_build_duplicate_form_message(key))

        block_proto = Block_pb2.Block()
        block_proto.form.form_id = form_id
        block_proto.form.clear_on_submit = clear_on_submit
        block_dg = self.dg._block(block_proto)

        # Attach the form's button info to the newly-created block's
        # DeltaGenerator.
        block_dg._form_data = FormData(form_id)
        return block_dg