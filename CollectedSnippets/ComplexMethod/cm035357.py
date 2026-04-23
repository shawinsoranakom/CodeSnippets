def _eq_no_pid(self, obj1: Event, obj2: Event) -> bool:
        if isinstance(obj1, IPythonRunCellAction) and isinstance(
            obj2, IPythonRunCellAction
        ):
            # for loop detection on edit actions, ignore the thought, compare some code
            # the code should have at least 3 lines, to avoid simple one-liners
            if (
                'edit_file_by_replace(' in obj1.code
                and 'edit_file_by_replace(' in obj2.code
            ):
                return (
                    len(obj1.code.split('\n')) > 2
                    and obj1.code.split('\n')[:3] == obj2.code.split('\n')[:3]
                )
            else:
                # default comparison
                return obj1 == obj2
        elif isinstance(obj1, CmdOutputObservation) and isinstance(
            obj2, CmdOutputObservation
        ):
            # for loop detection, ignore command_id, which is the pid
            return obj1.command == obj2.command and obj1.exit_code == obj2.exit_code
        else:
            # this is the default comparison
            return obj1 == obj2