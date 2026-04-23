def process_facebook_graphql_response(response_text, seen_post_ids, analysis_queue, queue_post_ids, conn):
    posts_processed = 0
    if not response_text:
        return posts_processed
    lines = response_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            json_obj = json.loads(line)
            if contains_facebook_posts(json_obj):
                parsed_posts = parse_facebook_posts(json_obj)
                if not parsed_posts:
                    continue
                normalized_posts = normalize_facebook_posts_batch(parsed_posts)
                for post_data in normalized_posts:
                    post_id = post_data.get("post_id")
                    if not post_id or post_id in seen_post_ids:
                        continue
                    seen_post_ids.add(post_id)
                    posts_processed += 1
                    needs_analysis = check_and_store_post(conn, post_data)
                    if needs_analysis and post_data.get("post_text"):
                        analysis_queue.append(post_data)
                        queue_post_ids.append(post_id)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error processing Facebook post: {e}")
            continue

    return posts_processed