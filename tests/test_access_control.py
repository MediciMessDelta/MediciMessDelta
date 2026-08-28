from api.access_control import (
    BRANCH_USER,
    MANAGING_DIRECTOR,
    can_access_branch,
    can_access_network,
    get_accessible_branches,
)


DIRECTOR = {
    "username": "director",
    "role": MANAGING_DIRECTOR,
    "branch": None,
}

FLORENCE_USER = {
    "username": "florence_manager",
    "role": BRANCH_USER,
    "branch": "Florence",
}


def test_managing_director_can_access_any_branch():
    assert can_access_branch(
        DIRECTOR,
        "Rome",
    )


def test_branch_user_can_access_assigned_branch():
    assert can_access_branch(
        FLORENCE_USER,
        "Florence",
    )


def test_branch_user_cannot_access_other_branch():
    assert not can_access_branch(
        FLORENCE_USER,
        "Rome",
    )


def test_managing_director_can_access_network():
    assert can_access_network(DIRECTOR)


def test_branch_user_cannot_access_network():
    assert not can_access_network(FLORENCE_USER)


def test_managing_director_can_access_all_branches():
    branches = [
        "Florence",
        "Rome",
        "Venice",
    ]

    assert get_accessible_branches(
        DIRECTOR,
        branches,
    ) == branches


def test_branch_user_only_sees_assigned_branch():
    branches = [
        "Florence",
        "Rome",
        "Venice",
    ]

    assert get_accessible_branches(
        FLORENCE_USER,
        branches,
    ) == ["Florence"]