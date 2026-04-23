def _normalize_query_type(self, query_type: str, query: str) -> str:
        """规范化查询类型"""
        if query_type in ["review", "recommend", "qa", "paper"]:
            return query_type

        query_lower = query.lower()
        for type_name, keywords in self.valid_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return type_name

        query_type_lower = query_type.lower()
        for type_name, keywords in self.valid_types.items():
            for keyword in keywords:
                if keyword in query_type_lower:
                    return type_name

        return "qa"