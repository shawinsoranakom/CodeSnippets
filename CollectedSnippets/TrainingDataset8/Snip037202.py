def show_wrapped_obj_warning():
        nonlocal has_shown_beta_warning
        if not has_shown_beta_warning:
            has_shown_beta_warning = True
            _show_beta_warning(obj_name, date)