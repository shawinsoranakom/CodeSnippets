def validate_json(prof, gc_collection_on):
            with TemporaryFileName(mode="w+") as fname:
                prof.export_chrome_trace(fname)
                with open(fname) as f:
                    events = json.load(f)["traceEvents"]
                    # Find required events
                    if gc_collection_on:
                        pre_gc = next(
                            (e for e in events if e["name"] == "pre_gc"), None
                        )
                        post_gc = next(
                            (e for e in events if e["name"] == "post_gc"), None
                        )
                        python_gc_events = [
                            e for e in events if e["name"] == "Python GC"
                        ]
                        # Assert all required events are present
                        self.assertIsNotNone(pre_gc, "pre_gc event is missing")
                        self.assertIsNotNone(post_gc, "post_gc event is missing")
                        self.assertTrue(
                            len(python_gc_events) > 0, "No Python GC events found"
                        )
                        # Calculate boundaries
                        pre_gc_end = pre_gc["ts"] + pre_gc.get("dur", 0)
                        post_gc_start = post_gc["ts"]
                        # Assert each Python GC event is correctly placed
                        for python_gc in python_gc_events:
                            python_gc_start = python_gc["ts"]
                            python_gc_end = python_gc["ts"] + python_gc.get("dur", 0)
                            self.assertTrue(
                                python_gc_start > pre_gc_end
                                and python_gc_end < post_gc_start,
                                f"Python GC event at {python_gc_start} is not correctly placed.",
                            )
                    else:
                        python_gc_events = [
                            e for e in events if e["name"] == "Python GC"
                        ]
                        self.assertTrue(
                            len(python_gc_events) == 0,
                            "Python GC event found when flag off",
                        )