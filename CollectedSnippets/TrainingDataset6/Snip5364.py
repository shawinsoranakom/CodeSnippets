def client_fixture() -> TestClient:
    from fastapi import Body
    from pydantic import Discriminator, Tag

    class Cat(BaseModel):
        pet_type: str = "cat"
        meows: int

    class Dog(BaseModel):
        pet_type: str = "dog"
        barks: float

    def get_pet_type(v):
        assert isinstance(v, dict)
        return v.get("pet_type", "")

    Pet = Annotated[
        Annotated[Cat, Tag("cat")] | Annotated[Dog, Tag("dog")],
        Discriminator(get_pet_type),
    ]

    app = FastAPI()

    @app.post("/pet/assignment")
    async def create_pet_assignment(pet: Pet = Body()):
        return pet

    @app.post("/pet/annotated")
    async def create_pet_annotated(pet: Annotated[Pet, Body()]):
        return pet

    client = TestClient(app)
    return client