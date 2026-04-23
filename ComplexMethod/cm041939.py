async def cr_by_points(self, patch: PatchSet, points: list[Point]):
        comments = []
        valid_patch_count = 0
        for patched_file in patch:
            if not patched_file:
                continue
            if patched_file.path.endswith(".py"):
                points = [p for p in points if p.language == "Python"]
                valid_patch_count += 1
            elif patched_file.path.endswith(".java"):
                points = [p for p in points if p.language == "Java"]
                valid_patch_count += 1
            else:
                continue
            group_points = [points[i : i + 3] for i in range(0, len(points), 3)]
            for group_point in group_points:
                points_str = "id description\n"
                points_str += "\n".join([f"{p.id} {p.text}" for p in group_point])
                prompt = CODE_REVIEW_PROMPT_TEMPLATE.format(patch=str(patched_file), points=points_str)
                resp = await self.llm.aask(prompt)
                json_str = parse_json_code_block(resp)[0]
                comments_batch = json.loads(json_str)
                if comments_batch:
                    patched_file_path = patched_file.path
                    for c in comments_batch:
                        c["commented_file"] = patched_file_path
                    comments.extend(comments_batch)

        if valid_patch_count == 0:
            raise ValueError("Only code reviews for Python and Java languages are supported.")

        return comments