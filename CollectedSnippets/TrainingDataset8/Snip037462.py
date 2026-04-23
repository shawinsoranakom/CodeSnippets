def _form_submit_button(
        self,
        label: str = "Submit",
        help: Optional[str] = None,
        on_click=None,
        args=None,
        kwargs=None,
        *,  # keyword-only arguments:
        type: Literal["primary", "secondary"] = "secondary",
        disabled: bool = False,
        ctx: Optional[ScriptRunContext] = None,
    ) -> bool:
        form_id = current_form_id(self.dg)
        submit_button_key = f"FormSubmitter:{form_id}-{label}"
        return self.dg._button(
            label=label,
            key=submit_button_key,
            help=help,
            is_form_submitter=True,
            on_click=on_click,
            args=args,
            kwargs=kwargs,
            type=type,
            disabled=disabled,
            ctx=ctx,
        )