def join_columns(self, columns: Columns) -> Columns:
        match self.join_mode:
            case JoinMode.SIMPLE:
                return (
                    columns[0],
                    *("Base " + x for x in columns[1:]),
                    *("Head " + x for x in columns[1:]),
                )
            case JoinMode.CHANGE | JoinMode.CHANGE_NO_SORT:
                return (
                    columns[0],
                    *("Base " + x for x in columns[1:]),
                    *("Head " + x for x in columns[1:]),
                ) + ("Change:",)
            case JoinMode.CHANGE_ONE_COLUMN:
                return (
                    columns[0],
                    "Base " + columns[1],
                    "Head " + columns[1],
                    "Change:",
                )