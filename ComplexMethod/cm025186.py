def washer_state(washer: Washer) -> str | None:
    """Determine correct states for a washer."""

    machine_state = washer.get_machine_state()

    if machine_state == WasherMachineState.RunningMainCycle:
        if washer.get_cycle_status_filling():
            return STATE_CYCLE_FILLING
        if washer.get_cycle_status_rinsing():
            return STATE_CYCLE_RINSING
        if washer.get_cycle_status_sensing():
            return STATE_CYCLE_SENSING
        if washer.get_cycle_status_soaking():
            return STATE_CYCLE_SOAKING
        if washer.get_cycle_status_spinning():
            return STATE_CYCLE_SPINNING
        if washer.get_cycle_status_washing():
            return STATE_CYCLE_WASHING

    return WASHER_MACHINE_STATE.get(machine_state)