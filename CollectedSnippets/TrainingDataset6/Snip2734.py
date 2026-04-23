def client_fixture() -> TestClient:
    from pydantic import BaseModel

    class Address(BaseModel):
        """
        This is a public description of an Address
        \f
        You can't see this part of the docstring, it's private!
        """

        line_1: str
        city: str
        state_province: str

    class Facility(BaseModel):
        id: str
        address: Address

    app = FastAPI()

    @app.get("/facilities/{facility_id}")
    def get_facility(facility_id: str) -> Facility:
        return Facility(
            id=facility_id,
            address=Address(line_1="123 Main St", city="Anytown", state_province="CA"),
        )

    client = TestClient(app)
    return client