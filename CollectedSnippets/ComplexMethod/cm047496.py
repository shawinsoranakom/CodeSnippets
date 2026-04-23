def convert_to_cache(self, value, record, validate=True):
        # cache format: tuple(ids)
        if isinstance(value, BaseModel):
            if validate and value._name != self.comodel_name:
                raise ValueError("Wrong value for %s: %s" % (self, value))
            ids = value._ids
            if record and not record.id:
                # x2many field value of new record is new records
                ids = tuple(it and NewId(it) for it in ids)
            return ids

        elif isinstance(value, (list, tuple)):
            # value is a list/tuple of commands, dicts or record ids
            comodel = record.env[self.comodel_name]
            # if record is new, the field's value is new records
            if record and not record.id:
                browse = lambda it: comodel.browse((it and NewId(it),))
            else:
                browse = comodel.browse
            # determine the value ids: in case of a real record or a new record
            # with origin, take its current value
            ids = OrderedSet(record[self.name]._ids if record._origin else ())
            # modify ids with the commands
            for command in value:
                if isinstance(command, (tuple, list)):
                    if command[0] == Command.CREATE:
                        ids.add(comodel.new(command[2], ref=command[1]).id)
                    elif command[0] == Command.UPDATE:
                        line = browse(command[1])
                        if validate:
                            line.update(command[2])
                        else:
                            line._update_cache(command[2], validate=False)
                        ids.add(line.id)
                    elif command[0] in (Command.DELETE, Command.UNLINK):
                        ids.discard(browse(command[1]).id)
                    elif command[0] == Command.LINK:
                        ids.add(browse(command[1]).id)
                    elif command[0] == Command.CLEAR:
                        ids.clear()
                    elif command[0] == Command.SET:
                        ids = OrderedSet(browse(it).id for it in command[2])
                elif isinstance(command, dict):
                    ids.add(comodel.new(command).id)
                else:
                    ids.add(browse(command).id)
            # return result as a tuple
            return tuple(ids)

        elif not value:
            return ()

        raise ValueError("Wrong value for %s: %s" % (self, value))