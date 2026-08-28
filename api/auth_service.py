import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

USER_FIXTURE_FILE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "users.json"
)


@lru_cache(maxsize=1)
def load_user_fixture():
    with open(
        USER_FIXTURE_FILE,
        "r",
        encoding="utf-8",
    ) as fixture_file:
        return json.load(fixture_file)


def authenticate_user(username, password):
    for user in load_user_fixture():
        if (
            user["username"] == username
            and user["password"] == password
        ):
            authenticated_user = deepcopy(user)
            authenticated_user.pop("password", None)
            return authenticated_user

    return None

def get_user(username):
    for user in load_user_fixture():
        if user["username"] == username:
            authenticated_user = deepcopy(user)
            authenticated_user.pop("password", None)
            return authenticated_user

    return None