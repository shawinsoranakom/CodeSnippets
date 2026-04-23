async def create_pet_annotated(pet: Annotated[Pet, Body()]):
        return pet