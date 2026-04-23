def test_crud_app(client: TestClient):
    # TODO: this warns that SQLModel.from_orm is deprecated in Pydantic v1, refactor
    # this if using obj.model_validate becomes independent of Pydantic v2
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        # No heroes before creating
        response = client.get("heroes/")
        assert response.status_code == 200, response.text
        assert response.json() == []

        # Create a hero
        response = client.post(
            "/heroes/",
            json={
                "id": 999,
                "name": "Dead Pond",
                "age": 30,
                "secret_name": "Dive Wilson",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json() == snapshot(
            {"age": 30, "secret_name": "Dive Wilson", "id": 999, "name": "Dead Pond"}
        )

        # Read a hero
        hero_id = response.json()["id"]
        response = client.get(f"/heroes/{hero_id}")
        assert response.status_code == 200, response.text
        assert response.json() == snapshot(
            {"name": "Dead Pond", "age": 30, "id": 999, "secret_name": "Dive Wilson"}
        )

        # Read all heroes
        # Create more heroes first
        response = client.post(
            "/heroes/",
            json={"name": "Spider-Boy", "age": 18, "secret_name": "Pedro Parqueador"},
        )
        assert response.status_code == 200, response.text
        response = client.post(
            "/heroes/", json={"name": "Rusty-Man", "secret_name": "Tommy Sharp"}
        )
        assert response.status_code == 200, response.text

        response = client.get("/heroes/")
        assert response.status_code == 200, response.text
        assert response.json() == snapshot(
            [
                {
                    "name": "Dead Pond",
                    "age": 30,
                    "id": IsInt(),
                    "secret_name": "Dive Wilson",
                },
                {
                    "name": "Spider-Boy",
                    "age": 18,
                    "id": IsInt(),
                    "secret_name": "Pedro Parqueador",
                },
                {
                    "name": "Rusty-Man",
                    "age": None,
                    "id": IsInt(),
                    "secret_name": "Tommy Sharp",
                },
            ]
        )

        response = client.get("/heroes/?offset=1&limit=1")
        assert response.status_code == 200, response.text
        assert response.json() == snapshot(
            [
                {
                    "name": "Spider-Boy",
                    "age": 18,
                    "id": IsInt(),
                    "secret_name": "Pedro Parqueador",
                }
            ]
        )

        # Delete a hero
        response = client.delete(f"/heroes/{hero_id}")
        assert response.status_code == 200, response.text
        assert response.json() == snapshot({"ok": True})

        response = client.get(f"/heroes/{hero_id}")
        assert response.status_code == 404, response.text

        response = client.delete(f"/heroes/{hero_id}")
        assert response.status_code == 404, response.text
        assert response.json() == snapshot({"detail": "Hero not found"})