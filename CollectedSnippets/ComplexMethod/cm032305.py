def update(self, condition: dict, new_value: dict, index_name: str, memory_id: str) -> bool:
        inf_conn = self.connPool.get_conn()
        try:
            db_instance = inf_conn.get_database(self.dbName)
            table_name = f"{index_name}_{memory_id}"
            table_instance = db_instance.get_table(table_name)

            columns = {}
            if table_instance:
                for n, ty, de, _ in table_instance.show_columns().rows():
                    columns[n] = (ty, de)
            condition_dict = {self.convert_condition_and_order_field(k): v for k, v in condition.items()}
            filter = self.equivalent_condition_to_str(condition_dict, table_instance)
            update_dict = {self.convert_message_field_to_infinity(k): v for k, v in new_value.items()}
            date_floats = {}
            for k, v in update_dict.items():
                if k in ["valid_at", "invalid_at", "forget_at"]:
                    date_floats[f"{k}_flt"] = date_string_to_timestamp(v) if v else 0
                elif self.field_keyword(k):
                    if isinstance(v, list):
                        update_dict[k] = "###".join(v)
                    else:
                        update_dict[k] = v
                elif k == "memory_id":
                    if isinstance(update_dict[k], list):
                        update_dict[k] = update_dict[k][0]  # since d[k] is a list, but we need a str
                else:
                    update_dict[k] = v
            if date_floats:
                update_dict.update(date_floats)

            self.logger.debug(f"INFINITY update table {table_name}, filter {filter}, newValue {new_value}.")
            table_instance.update(filter, update_dict)
        finally:
            self.connPool.release_conn(inf_conn)
        return True