def write_batch(self, records_commands_list: Sequence[tuple[BaseModel, typing.Any]], create: bool = False) -> None:
        if not records_commands_list:
            return

        for idx, (recs, value) in enumerate(records_commands_list):
            if isinstance(value, tuple):
                value = [Command.set(value)]
            elif isinstance(value, BaseModel) and value._name == self.comodel_name:
                value = [Command.set(value._ids)]
            elif value is False or value is None:
                value = [Command.clear()]
            elif isinstance(value, list) and value and not isinstance(value[0], (tuple, list)):
                value = [Command.set(tuple(value))]
            if not isinstance(value, list):
                raise ValueError("Wrong value for %s: %s" % (self, value))
            records_commands_list[idx] = (recs, value)

        record_ids = {rid for recs, cs in records_commands_list for rid in recs._ids}
        if all(record_ids):
            self.write_real(records_commands_list, create)
        else:
            assert not any(record_ids), f"{records_commands_list} contains a mix of real and new records. It is not supported."
            self.write_new(records_commands_list)