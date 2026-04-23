def sql_side_effect(query):
            if "SELECT 1" in query:
                return mock_result1
            elif "information_schema.tables" in query:
                return mock_result2
            elif "__all_disk_stat" in query:
                return mock_result3
            elif "SHOW PROCESSLIST" in query:
                return mock_result4
            elif "SHOW VARIABLES LIKE 'max_connections'" in query:
                return mock_result4
            elif "information_schema.processlist" in query and "time >" in query:
                return mock_result5
            elif "information_schema.processlist" in query and "COUNT" in query:
                return mock_result6
            return Mock()