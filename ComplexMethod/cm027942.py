async def analyze_finances(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = f"finance_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            initial_state = {
                "monthly_income": financial_data.get("monthly_income", 0),
                "dependants": financial_data.get("dependants", 0),
                "transactions": financial_data.get("transactions", []),
                "manual_expenses": financial_data.get("manual_expenses", {}),
                "debts": financial_data.get("debts", [])
            }

            session = self.session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
                state=initial_state
            )

            if session.state.get("transactions"):
                self._preprocess_transactions(session)

            if session.state.get("manual_expenses"):
                self._preprocess_manual_expenses(session)

            default_results = self._create_default_results(financial_data)

            user_content = types.Content(
                role='user',
                parts=[types.Part(text=json.dumps(financial_data))]
            )

            async for event in self.runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=user_content
            ):
                if event.is_final_response() and event.author == self.coordinator_agent.name:
                    break

            updated_session = self.session_service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id
            )

            results = {}
            for key in ["budget_analysis", "savings_strategy", "debt_reduction"]:
                value = updated_session.state.get(key)
                results[key] = parse_json_safely(value, default_results[key]) if value else default_results[key]

            return results

        except Exception as e:
            logger.exception(f"Error during finance analysis: {str(e)}")
            raise
        finally:
            self.session_service.delete_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id
            )