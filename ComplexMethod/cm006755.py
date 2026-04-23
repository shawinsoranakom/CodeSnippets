def step_callback(agent_output) -> None:
            id_ = self._vertex.id if self._vertex else self.display_name
            if isinstance(agent_output, AgentFinish):
                messages = agent_output.messages
                self.log(cast("dict", messages[0].to_json()), name=f"Finish (Agent: {id_})")
            elif isinstance(agent_output, list):
                messages_dict_ = {f"Action {i}": action.messages for i, (action, _) in enumerate(agent_output)}
                # Serialize the messages with to_json() to avoid issues with circular references
                serializable_dict = {k: [m.to_json() for m in v] for k, v in messages_dict_.items()}
                messages_dict = {k: v[0] if len(v) == 1 else v for k, v in serializable_dict.items()}
                self.log(messages_dict, name=f"Step (Agent: {id_})")