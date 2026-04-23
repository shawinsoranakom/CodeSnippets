async def run_optimization():
        logger.info(f"Starting optimization for session {session_id}")
        optimizer = SkillOptimizer(api_key=gemini_key)

        async def callback(event):
            logger.info(f"Callback event: {event['type']}")
            if "event_queue" in session:
                await session["event_queue"].put(event)
            if event["type"] == "baseline":
                session["experiments"].append({
                    "experiment_id": 0,
                    "pass_rate": event["data"].get("score", 0),
                    "status": "baseline",
                    "per_eval": event["data"].get("per_eval", []),
                })
            elif event["type"] == "experiment_result":
                session["experiments"].append({
                    "experiment_id": event["data"].get("round", len(session["experiments"])),
                    "pass_rate": event["data"].get("score", 0),
                    "status": "keep" if event["data"].get("kept") else "discard",
                    "per_eval": event["data"].get("per_eval", []),
                    "description": event["data"].get("description", ""),
                    "strategy": event["data"].get("strategy", ""),
                })
            elif event["type"] == "complete":
                session["status"] = "complete"
                data = event["data"]
                ml = data.get("mutation_log", [])
                # Transform to match frontend ResultsStep expectations
                session["final_result"] = {
                    "baseline_score": data.get("baseline_score", 0),
                    "final_score": data.get("final_score", 0),
                    "improved_skill_md": data.get("improved_skill_md", ""),
                    "original_skill_md": session.get("original_skill_md", ""),
                    "score_history": data.get("score_history", []),
                    "experiments_run": len(ml),
                    "kept": sum(1 for m in ml if m.get("kept")),
                    "discarded": sum(1 for m in ml if not m.get("kept")),
                    "changelog": [
                        {
                            "description": m.get("description", m.get("diagnosis", "")),
                            "reasoning": m.get("diagnosis", ""),
                            "status": "keep" if m.get("kept") else "discard",
                            "score_before": m.get("score_before", 0),
                            "score_after": m.get("score_after", 0),
                            "strategy": m.get("strategy_type", ""),
                        }
                        for m in ml
                    ],
                    "mutation_log": ml,
                    "strategy_stats": data.get("strategy_stats", {}),
                }
                session["current_skill_md"] = data.get("improved_skill_md", "")
                if "event_queue" in session:
                    await session["event_queue"].put(None)

        try:
            result = await optimizer.optimize(
                skill_files=session["skill_files"],
                scenarios=session["scenarios"],
                evals=session["evals"],
                max_rounds=request.max_rounds,
                callback=callback,
            )
            logger.info(f"Optimization complete: {result['baseline_score']}% -> {result['final_score']}%")
            # Don't overwrite final_result if callback already set it with transformed data
            if not session.get("final_result"):
                ml = result.get("mutation_log", [])
                session["final_result"] = {
                    "baseline_score": result.get("baseline_score", 0),
                    "final_score": result.get("final_score", 0),
                    "improved_skill_md": result.get("improved_skill_md", ""),
                    "original_skill_md": session.get("original_skill_md", ""),
                    "score_history": result.get("score_history", []),
                    "experiments_run": len(ml),
                    "kept": sum(1 for m in ml if m.get("kept")),
                    "discarded": sum(1 for m in ml if not m.get("kept")),
                    "changelog": [
                        {
                            "description": m.get("description", m.get("diagnosis", "")),
                            "reasoning": m.get("diagnosis", ""),
                            "status": "keep" if m.get("kept") else "discard",
                            "score_before": m.get("score_before", 0),
                            "score_after": m.get("score_after", 0),
                            "strategy": m.get("strategy_type", ""),
                        }
                        for m in ml
                    ],
                    "mutation_log": ml,
                }
            session["current_skill_md"] = result["improved_skill_md"]
            session["status"] = "complete"
        except Exception as e:
            logger.error(f"Optimization error: {traceback.format_exc()}")
            session["status"] = "error"
            session["error"] = str(e)
            if "event_queue" in session:
                await session["event_queue"].put({"type": "error", "data": {"message": str(e)}})
                await session["event_queue"].put(None)