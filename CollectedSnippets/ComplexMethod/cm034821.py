def find_media(search: str):
            safe_search = [secure_filename(chunk.lower()) for chunk in search.split("+")]
            media_dir = get_media_dir()
            if not os.access(media_dir, os.R_OK):
                return jsonify({"error": {"message": "Not found"}}), 404
            if search not in self.match_files:
                self.match_files[search] = {}
                found_mime_type = False
                for root, _, files in os.walk(media_dir):
                    for file in files:
                        mime_type = is_allowed_extension(file)
                        if mime_type is not None:
                            mime_type = secure_filename(mime_type)
                            if safe_search[0] in mime_type:
                                found_mime_type = True
                                self.match_files[search][file] = self.match_files[search].get(file, 0) + 1
                        for tag in safe_search[1:] if found_mime_type else safe_search:
                            if tag in file.lower():
                                self.match_files[search][file] = self.match_files[search].get(file, 0) + 1
                    break
            match_files = [file for file, count in self.match_files[search].items() if count >= request.args.get("min", len(safe_search))]
            if int(request.args.get("skip") or 0) >= len(match_files):
                return jsonify({"error": {"message": "Not found"}}), 404
            if (request.args.get("random", False)):
                seed = request.args.get("random")
                if seed not in ["true", "True", "1"]:
                   random.seed(seed)
                return redirect(f"/media/{random.choice(match_files)}"), 302
            return redirect(f"/media/{match_files[int(request.args.get('skip') or 0)]}", 302)