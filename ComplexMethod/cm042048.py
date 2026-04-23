async def _get_class_view(self, ns_class_name: str) -> _VisualClassView:
        """Returns the Markdown Mermaid class diagram code block object for the specified class."""
        rows = await self.graph_db.select(subject=ns_class_name)
        class_view = _VisualClassView(package=ns_class_name)
        for r in rows:
            if r.predicate == GraphKeyword.HAS_CLASS_VIEW:
                class_view.uml = UMLClassView.model_validate_json(r.object_)
            elif r.predicate == GraphKeyword.IS + GENERALIZATION + GraphKeyword.OF:
                name = split_namespace(r.object_)[-1]
                name = self._refine_name(name)
                if name:
                    class_view.generalizations.append(name)
            elif r.predicate == GraphKeyword.IS + COMPOSITION + GraphKeyword.OF:
                name = split_namespace(r.object_)[-1]
                name = self._refine_name(name)
                if name:
                    class_view.compositions.append(name)
            elif r.predicate == GraphKeyword.IS + AGGREGATION + GraphKeyword.OF:
                name = split_namespace(r.object_)[-1]
                name = self._refine_name(name)
                if name:
                    class_view.aggregations.append(name)
        return class_view