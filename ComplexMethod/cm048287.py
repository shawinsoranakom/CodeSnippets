def _read_group_orderby(self, order: str, groupby_terms: dict[str, SQL], query: Query) -> SQL:
        if "day_number" not in groupby_terms:
            return super()._read_group_orderby(order, groupby_terms, query)
        if not order:
            order = ",".join(groupby_terms)
        order_parts = [part.strip() for part in order.split(",")]
        day_number_part = next((part for part in order_parts if part.startswith("day_number")), None)
        other_parts = [part for part in order_parts if not part.startswith("day_number")]
        other_groupby_terms = {k: v for k, v in groupby_terms.items() if k != "day_number"}
        other_order = ",".join(other_parts) if other_parts else None
        other_orderby = None
        if other_order or other_groupby_terms:
            other_orderby = super()._read_group_orderby(other_order, other_groupby_terms, query)
            groupby_terms.update(other_groupby_terms)
            if query._order_groupby:
                groupby_terms["day_number"] = SQL(", ").join([groupby_terms["day_number"], *query._order_groupby])
                query._order_groupby.clear()
        if not day_number_part:
            return other_orderby
        parts = [p.upper() for p in day_number_part.split()]
        direction = next((p for p in parts if p in ("ASC", "DESC")), "ASC")
        nulls_parts = [p for p in parts if p in ("NULLS", "FIRST", "LAST")]
        sql_direction = SQL("ASC") if direction == "ASC" else SQL("DESC")
        if "NULLS" in nulls_parts and "FIRST" in nulls_parts:
            sql_nulls = SQL("NULLS FIRST")
        elif "NULLS" in nulls_parts and "LAST" in nulls_parts:
            sql_nulls = SQL("NULLS LAST")
        else:
            sql_nulls = SQL()
        first_week_day = int(get_lang(self.env).week_start)
        day_number_orderby = SQL(
            "mod(7 - %s + (%s)::int, 7) %s %s",
            first_week_day,
            groupby_terms["day_number"],
            sql_direction,
            sql_nulls
        )
        return SQL(", ").join([day_number_orderby, other_orderby]) if other_orderby else day_number_orderby