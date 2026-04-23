def check_events():
            if len(events) != num_events:
                msg = f"DynamoDB updates retrieved (actual/expected): {len(events)}/{num_events}"
                LOGGER.warning(msg)
            assert len(events) == num_events
            event_items = [json.loads(base64.b64decode(e["data"])) for e in events]
            # make sure that we have the right amount of expected event types
            inserts = [e for e in event_items if e.get("__action_type") == "INSERT"]
            modifies = [e for e in event_items if e.get("__action_type") == "MODIFY"]
            removes = [e for e in event_items if e.get("__action_type") == "REMOVE"]
            assert len(inserts) == num_insert
            assert len(modifies) == num_modify
            assert len(removes) == num_delete

            # assert that all inserts were received

            for i, event in enumerate(inserts):
                assert "old_image" not in event
                item_id = f"testId{i:d}"
                matching = [i for i in inserts if i["new_image"]["id"] == item_id][0]
                assert matching["new_image"] == {"id": item_id, "data": "foobar123"}

            # assert that all updates were received

            def assert_updates(expected_updates, modifies):
                def found(update):
                    for modif in modifies:
                        if modif["old_image"]["id"] == update["id"]:
                            assert modif["old_image"] == {
                                "id": update["id"],
                                "data": update["old"],
                            }
                            assert modif["new_image"] == {
                                "id": update["id"],
                                "data": update["new"],
                            }
                            return True

                for update in expected_updates:
                    assert found(update)

            updates1 = [
                {"id": "testId6", "old": "foobar123", "new": "foobar123_updated1"},
                {"id": "testId7", "old": "foobar123", "new": "foobar123_updated1"},
            ]
            updates2 = [
                {
                    "id": "testId6",
                    "old": "foobar123_updated1",
                    "new": "foobar123_updated2",
                },
                {
                    "id": "testId7",
                    "old": "foobar123_updated1",
                    "new": "foobar123_updated2",
                },
                {"id": "testId8", "old": "foobar123", "new": "foobar123_updated2"},
            ]

            assert_updates(updates1, modifies[:2])
            assert_updates(updates2, modifies[2:])

            # assert that all removes were received

            for i, event in enumerate(removes):
                assert "new_image" not in event
                item_id = f"testId{i:d}"
                matching = [i for i in removes if i["old_image"]["id"] == item_id][0]
                assert matching["old_image"] == {"id": item_id, "data": "foobar123"}