def test_mutated_expression_deep(func):
        func.source_expressions[1].value[0] = "mutated"