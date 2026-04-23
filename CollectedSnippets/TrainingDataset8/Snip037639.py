def check_callback_rules(
    dg: "DeltaGenerator", on_change: Optional[WidgetCallback]
) -> None:
    if runtime.exists() and is_in_form(dg) and on_change is not None:
        raise StreamlitAPIException(
            "With forms, callbacks can only be defined on the `st.form_submit_button`."
            " Defining callbacks on other widgets inside a form is not allowed."
        )