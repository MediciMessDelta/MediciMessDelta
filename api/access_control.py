from api.auth_service import load_user_fixture


MANAGING_DIRECTOR = "MANAGING_DIRECTOR"
BRANCH_USER = "BRANCH_USER"


def get_current_user(request):
    username = request.headers.get("X-User")

    if not username:
        return None

    for user in load_user_fixture():
        if user["username"] == username:
            return {
                key: value
                for key, value in user.items()
                if key != "password"
            }

    return None


def can_access_branch(user, branch):
    if not user:
        return False

    if user["role"] == MANAGING_DIRECTOR:
        return True

    if user["role"] == BRANCH_USER:
        return user["branch"] == branch

    return False


def can_access_network(user):
    if not user:
        return False

    return user["role"] == MANAGING_DIRECTOR


def get_accessible_branches(user, branches):
    if not user:
        return []

    if user["role"] == MANAGING_DIRECTOR:
        return list(branches)

    if user["role"] == BRANCH_USER:
        return [
            branch
            for branch in branches
            if branch == user["branch"]
        ]

    return []