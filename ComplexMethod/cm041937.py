def format_comments(self, comments: list[dict], points: list[Point], patch: PatchSet):
        new_comments = []
        logger.debug(f"original comments: {comments}")
        for cmt in comments:
            try:
                if cmt.get("commented_file").endswith(".py"):
                    points = [p for p in points if p.language == "Python"]
                elif cmt.get("commented_file").endswith(".java"):
                    points = [p for p in points if p.language == "Java"]
                else:
                    continue
                for p in points:
                    point_id = int(cmt.get("point_id", -1))
                    if point_id == p.id:
                        code_start_line = cmt.get("code_start_line")
                        code_end_line = cmt.get("code_end_line")
                        code = get_code_block_from_patch(patch, code_start_line, code_end_line)

                        new_comments.append(
                            {
                                "commented_file": cmt.get("commented_file"),
                                "code": code,
                                "code_start_line": code_start_line,
                                "code_end_line": code_end_line,
                                "comment": cmt.get("comment"),
                                "point_id": p.id,
                                "point": p.text,
                                "point_detail": p.detail,
                            }
                        )
                        break
            except Exception:
                pass

        logger.debug(f"new_comments: {new_comments}")
        return new_comments