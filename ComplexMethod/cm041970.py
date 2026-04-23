def determine_decomp(act_desp, act_dura):
        """
        Given an action description and its duration, we determine whether we need
        to decompose it. If the action is about the agent sleeping, we generally
        do not want to decompose it, so that's what we catch here.

        INPUT:
        act_desp: the description of the action (e.g., "sleeping")
        act_dura: the duration of the action in minutes.
        OUTPUT:
        a boolean. True if we need to decompose, False otherwise.
        """
        if "sleep" not in act_desp and "bed" not in act_desp:
            return True
        elif "sleeping" in act_desp or "asleep" in act_desp or "in bed" in act_desp:
            return False
        elif "sleep" in act_desp or "bed" in act_desp:
            if act_dura > 60:
                return False
        return True