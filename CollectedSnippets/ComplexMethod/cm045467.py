def test_cascade_delete(self, test_db: DatabaseManager, test_user: str):
        """Test all levels of cascade delete"""
        # Enable foreign keys for SQLite (crucial for cascade delete)
        with Session(test_db.engine) as session:
            session.execute(text("PRAGMA foreign_keys=ON"))
            session.commit()

        # Test Run -> Message cascade
        team1 = Team(user_id=test_user, component={"name": "Team1", "type": "team"})
        test_db.upsert(team1)
        session1 = SessionModel(user_id=test_user, team_id=team1.id, name="Session1")
        test_db.upsert(session1)
        run1_id = 1
        test_db.upsert(Run(
            id=run1_id, 
            user_id=test_user, 
            session_id=session1.id or 1,  # Ensure session_id is not None
            status=RunStatus.COMPLETE, 
            task=MessageConfig(content="Task1", source="user").model_dump()
        ))
        test_db.upsert(Message(
            user_id=test_user, 
            session_id=session1.id, 
            run_id=run1_id, 
            config=MessageConfig(content="Message1", source="assistant").model_dump()
        ))

        test_db.delete(Run, {"id": run1_id})
        db_message = test_db.get(Message, {"run_id": run1_id})
        if db_message.data:
            assert len(db_message.data) == 0, "Run->Message cascade failed"

        # Test Session -> Run -> Message cascade
        session2 = SessionModel(user_id=test_user, team_id=team1.id, name="Session2")
        test_db.upsert(session2)
        run2_id = 2
        test_db.upsert(Run(
            id=run2_id, 
            user_id=test_user, 
            session_id=session2.id or 2,  # Ensure session_id is not None
            status=RunStatus.COMPLETE, 
            task=MessageConfig(content="Task2", source="user").model_dump()
        ))
        test_db.upsert(Message(
            user_id=test_user, 
            session_id=session2.id, 
            run_id=run2_id, 
            config=MessageConfig(content="Message2", source="assistant").model_dump()
        ))

        test_db.delete(SessionModel, {"id": session2.id})
        session = test_db.get(SessionModel, {"id": session2.id})
        run = test_db.get(Run, {"id": run2_id})
        if session.data:
            assert len(session.data) == 0, "Session->Run cascade failed"
        if run.data:
            assert len(run.data) == 0, "Session->Run->Message cascade failed"

        # Clean up
        test_db.delete(Team, {"id": team1.id})