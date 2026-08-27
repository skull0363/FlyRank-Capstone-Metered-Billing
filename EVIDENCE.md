
=================== test session starts ===================
platform win32 -- Python 3.13.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ethan\OneDrive\Documents\GitHub\FlyRank Capstone Metered Billing
plugins: anyio-4.14.2
collected 0 items                                          

==================== warnings summary =====================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\ethan\OneDrive\Documents\GitHub\FlyRank CapstoneMetered Billing\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

app\config.py:3
  C:\Users\ethan\OneDrive\Documents\GitHub\FlyRank CapstoneMetered Billing\app\config.py:3: PydanticDeprecatedSince20:Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class Settings(BaseSettings):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================== 2 warnings in 0.09s ===================
(venv) 