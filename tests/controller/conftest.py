from typing import Generator

import pytest
from starlette.testclient import TestClient

from main import app


@pytest.fixture()
def api_client() -> Generator[TestClient, None, None]:
    yield TestClient(app)
