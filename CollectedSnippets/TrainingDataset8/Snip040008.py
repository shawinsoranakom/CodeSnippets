def _create_widget(id, states):
    states.widgets.add().id = id
    return states.widgets[-1]