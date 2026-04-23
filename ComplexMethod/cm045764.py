def get_hit_index(
            returned_docs: list[str], labels: list[str] | None
        ) -> int | None:
            """
            Returns hit index for a label for returned docs.
            Assumes single ground truth text/phrase.
            Uses string intersection with percentage to decide.
            Returns `None` if not found.
            """
            if labels is None:
                return None

            def compare_intersect(pred: str, label: str) -> float:
                intersect_len = len(set(label.split(" ")).intersection(pred.split(" ")))
                return intersect_len / len(set(label.split(" ")))

            for idx, t in enumerate(returned_docs):
                if t and str(labels) != "nan" and labels:
                    try:
                        cartesian = list(product([t], labels))
                        sim_pass = list(
                            map(lambda x: compare_intersect(x[0], x[1]), cartesian)
                        )

                        if max(sim_pass) >= STRDIFF_MIN_SIMILARITY:
                            return idx
                    except Exception:
                        print("label empty:", labels)

            return None