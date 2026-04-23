def report(
        self, other: Optional["JsonProfile"] = None, name_limit: int = 40
    ) -> str:
        def create_ret(
            table_headers: list[str], table_rows: dict[str, list[str]]
        ) -> str:
            table_flattened = [
                [kernel_name[:name_limit], *kernel_vals]
                for kernel_name, kernel_vals in table_rows.items()
            ]
            return tabulate_2d(table_flattened, headers=table_headers)

        if other is not None:
            self._compute_stats()
            other._compute_stats()

            self_tables = self._create_tables(self._devices)
            other_tables = self._create_tables(other._devices)

            self_name = (
                self.benchmark_name if self.benchmark_name is not None else "Table 1"
            )
            other_name = (
                other.benchmark_name if other.benchmark_name is not None else "Table 2"
            )

            ret = []
            assert self._devices.keys() == other._devices.keys()
            for device_idx, t1, t2 in zip_dicts(
                self_tables, other_tables, d1_default=None, d2_default=None
            ):
                assert t1 is not None
                assert t2 is not None
                table_headers, table_rows = self._combine_tables(
                    t1, self_name, t2, other_name
                )
                tab_string = create_ret(table_headers, table_rows)
                # pyrefly: ignore [bad-argument-type]
                ret.append(f"{self._devices[device_idx]}:\n{tab_string}")
            return "\n".join(ret)
        self._compute_stats()

        self_tables = self._create_tables(self._devices)

        ret = []
        for idx, table in self_tables.items():
            table_headers, table_rows = table
            tab_string = create_ret(table_headers, table_rows)
            # pyrefly: ignore [bad-argument-type]
            ret.append(f"{self._devices[idx]}:\n{tab_string}")
        return "\n".join(ret)