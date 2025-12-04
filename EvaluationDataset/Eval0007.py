class AppState(Stateful):
    """Wrapper for checkpointing the Application State including model and optimizer."""

    def __init__(self, model, optimizer=None):
        self.model = model
        self.optimizer = optimizer

    def state_dict(self):
        model_state_dict, optimizer_state_dict = get_state_dict(self.model, self.optimizer)
        return {"model": model_state_dict, "optim": optimizer_state_dict}

    def load_state_dict(self, state_dict):
        set_state_dict(
            self.model, self.optimizer, model_state_dict=state_dict["model"], optim_state_dict=state_dict["optim"]
        )
