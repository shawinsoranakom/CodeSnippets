def visitComparison_composite(
        self, ctx: ASLParser.Comparison_compositeContext
    ) -> ComparisonComposite:
        choice_op: ComparisonComposite.ChoiceOp = self.visit(ctx.choice_operator())
        rules: list[ChoiceRule] = []
        for child in ctx.children[1:]:
            cmp: Component | None = self.visit(child)
            if not cmp:
                continue
            elif isinstance(cmp, ChoiceRule):
                rules.append(cmp)

        match choice_op:
            case ComparisonComposite.ChoiceOp.Not:
                if len(rules) != 1:
                    raise ValueError(
                        f"ComparisonCompositeNot must carry only one ComparisonCompositeStmt in: '{ctx.getText()}'."
                    )
                return ComparisonCompositeNot(rule=rules[0])
            case ComparisonComposite.ChoiceOp.And:
                return ComparisonCompositeAnd(rules=rules)
            case ComparisonComposite.ChoiceOp.Or:
                return ComparisonCompositeOr(rules=rules)