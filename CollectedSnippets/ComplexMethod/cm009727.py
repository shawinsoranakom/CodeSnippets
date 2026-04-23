def _check_posts(self) -> None:
        posts = _get_posts(self.tracer.client)
        name_order = [
            "parent",
            "RunnableSequence",
            "before",
            "RunnableParallel<chain_result,other_thing>",
            ["my_child_function", "other_thing"],
            "after",
        ]
        expected_parents = {
            "parent": None,
            "RunnableSequence": "parent",
            "before": "RunnableSequence",
            "RunnableParallel<chain_result,other_thing>": "RunnableSequence",
            "my_child_function": "RunnableParallel<chain_result,other_thing>",
            "other_thing": "RunnableParallel<chain_result,other_thing>",
            "after": "RunnableSequence",
        }
        assert len(posts) == sum(
            1 if isinstance(n, str) else len(n) for n in name_order
        )
        prev_dotted_order = None
        dotted_order_map = {}
        id_map = {}
        parent_id_map = {}
        i = 0
        for name in name_order:
            if isinstance(name, list):
                for n in name:
                    matching_post = next(
                        p for p in posts[i : i + len(name)] if p["name"] == n
                    )
                    assert matching_post
                    dotted_order = matching_post["dotted_order"]
                    if prev_dotted_order is not None:
                        assert dotted_order > prev_dotted_order
                    dotted_order_map[n] = dotted_order
                    id_map[n] = matching_post["id"]
                    parent_id_map[n] = matching_post.get("parent_run_id")
                i += len(name)
                continue
            assert posts[i]["name"] == name
            dotted_order = posts[i]["dotted_order"]
            if prev_dotted_order is not None and not str(
                expected_parents[name]  # type: ignore[index]
            ).startswith("RunnableParallel"):
                assert dotted_order > prev_dotted_order, (
                    f"{name} not after {name_order[i - 1]}"
                )
            prev_dotted_order = dotted_order
            if name in dotted_order_map:
                msg = f"Duplicate name {name}"
                raise ValueError(msg)
            dotted_order_map[name] = dotted_order
            id_map[name] = posts[i]["id"]
            parent_id_map[name] = posts[i].get("parent_run_id")
            i += 1

        # Now check the dotted orders
        for name, parent_ in expected_parents.items():
            dotted_order = dotted_order_map[name]
            if parent_ is not None:
                parent_dotted_order = dotted_order_map[parent_]
                assert dotted_order.startswith(parent_dotted_order), (
                    f"{name}, {parent_dotted_order} not in {dotted_order}"
                )
                assert str(parent_id_map[name]) == str(id_map[parent_])
            else:
                assert dotted_order.split(".")[0] == dotted_order