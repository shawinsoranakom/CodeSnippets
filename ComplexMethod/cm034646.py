def sync_record_model_feedback(
    scraper: CloudScraper,
    account: Dict[str, Any],
    reward_kw: Dict[str, str]
) -> Optional[str]:
    try:
        url = "https://yupp.ai/api/trpc/evals.getTurnAnnotations"
        payload = {"0": {"json": {"turnId": reward_kw["turn_id"]}}}
        scraper.cookies.set("__Secure-yupp.session-token", account["token"])
        response = scraper.get(url, params={"batch": "1", "input": json.dumps(payload)})
        data = response.json()
        positive_notes = []
        for result in data:
            json_data = result.get("result", {}).get("data", {}).get("json", {})
            positive_notes = [row[0] for row in json_data.get("positive_notes", [])]
        positive_notes = [random.choice(positive_notes)] if positive_notes else []
        log_debug(f"Recording feedback for turn {reward_kw['turn_id']}: {positive_notes}")
        url = "https://yupp.ai/api/trpc/evals.recordModelFeedback?batch=1"
        selected_message_id = reward_kw.get("left_message_id") if reward_kw.get("selection") == "left" else reward_kw.get("right_message_id")
        variant_message_id = reward_kw.get("right_message_id") if reward_kw.get("selection") == "left" else reward_kw.get("left_message_id")
        payload = {"0":{"json":{"turnId":reward_kw["turn_id"],"isOnboarding":False,"evalType":"SELECTION","messageEvals":[
            {"messageId":selected_message_id,"rating":"GOOD","reasons":positive_notes},
            {"messageId":variant_message_id,"rating":"BAD","reasons":[]}
        ],"comment":"","requireReveal":False}}}

        response = scraper.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        for result in data:
            json_data = result.get("result", {}).get("data", {}).get("json", {})
            eval_id = json_data.get("evalId")
            final_reward = json_data.get("finalRewardAmount")
            log_debug(f"Feedback recorded - evalId: {eval_id}, reward: {final_reward}")

            if final_reward:
                return eval_id
        return None
    except Exception as e:
        log_debug(f"Failed to record model feedback. Error: {e}")
        return None