def _get_over_max_options_message(current_selections: int, max_selections: int):
    curr_selections_noun = "option" if current_selections == 1 else "options"
    max_selections_noun = "option" if max_selections == 1 else "options"
    return f"""
Multiselect has {current_selections} {curr_selections_noun} selected but `max_selections`
is set to {max_selections}. This happened because you either gave too many options to `default`
or you manipulated the widget's state through `st.session_state`. Note that
the latter can happen before the line indicated in the traceback.
Please select at most {max_selections} {max_selections_noun}.
"""