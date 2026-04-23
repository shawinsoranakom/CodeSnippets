def from_action(cls, action: Self | str | ChangeAction) -> Self:
        if isinstance(action, cls):
            return action

        # only used in CFn
        if isinstance(action, ChangeAction):
            action = action.value

        match action:
            case "Add":
                return cls.CREATE
            case "Modify" | "Dynamic":
                return cls.UPDATE
            case "Remove":
                return cls.DELETE
            case "Read":
                return cls.READ
            case "List":
                return cls.LIST
            case _:
                available_values = [every.value for every in cls]
                raise ValueError(
                    f"Invalid action option '{action}', should be one of {available_values}"
                )