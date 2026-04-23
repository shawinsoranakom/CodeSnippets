def Depends(  # noqa: N802
    dependency: Annotated[
        Callable[..., Any] | None,
        Doc(
            """
            A "dependable" callable (like a function).

            Don't call it directly, FastAPI will call it for you, just pass the object
            directly.

            Read more about it in the
            [FastAPI docs for Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
            """
        ),
    ] = None,
    *,
    use_cache: Annotated[
        bool,
        Doc(
            """
            By default, after a dependency is called the first time in a request, if
            the dependency is declared again for the rest of the request (for example
            if the dependency is needed by several dependencies), the value will be
            re-used for the rest of the request.

            Set `use_cache` to `False` to disable this behavior and ensure the
            dependency is called again (if declared more than once) in the same request.

            Read more about it in the
            [FastAPI docs about sub-dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/sub-dependencies/#using-the-same-dependency-multiple-times)
            """
        ),
    ] = True,
    scope: Annotated[
        Literal["function", "request"] | None,
        Doc(
            """
            Mainly for dependencies with `yield`, define when the dependency function
            should start (the code before `yield`) and when it should end (the code
            after `yield`).

            * `"function"`: start the dependency before the *path operation function*
                that handles the request, end the dependency after the *path operation
                function* ends, but **before** the response is sent back to the client.
                So, the dependency function will be executed **around** the *path operation
                **function***.
            * `"request"`: start the dependency before the *path operation function*
                that handles the request (similar to when using `"function"`), but end
                **after** the response is sent back to the client. So, the dependency
                function will be executed **around** the **request** and response cycle.

            Read more about it in the
            [FastAPI docs for FastAPI Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#early-exit-and-scope)
            """
        ),
    ] = None,
) -> Any:
    """
    Declare a FastAPI dependency.

    It takes a single "dependable" callable (like a function).

    Don't call it directly, FastAPI will call it for you.

    Read more about it in the
    [FastAPI docs for Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/).

    **Example**

    ```python
    from typing import Annotated

    from fastapi import Depends, FastAPI

    app = FastAPI()


    async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
        return {"q": q, "skip": skip, "limit": limit}


    @app.get("/items/")
    async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
        return commons
    ```
    """
    return params.Depends(dependency=dependency, use_cache=use_cache, scope=scope)