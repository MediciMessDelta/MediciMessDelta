from datetime import datetime

from flask import Flask, jsonify, request

from api.access_control import can_access_branch
from api.alert_service import acknowledge_alert, get_alerts
from api.auth_service import authenticate_user, get_user
from api.cashflow_service import get_cashflow
from api.data_service import get_transaction_page
from api.expense_service import get_expense_breakdown
from api.kpi_service import get_kpi_summary
from api.loan_service import get_loan_portfolio


def create_app():
    app = Flask(__name__)

    def authorize_branch(username, branch):
        if not username:
            return jsonify(
                {
                    "error": "username is required"
                }
            ), 401

        user = get_user(username)

        if user is None:
            return jsonify(
                {
                    "error": "unknown user"
                }
            ), 401

        if not can_access_branch(user, branch):
            return jsonify(
                {
                    "error": "user is not authorized for this branch"
                }
            ), 403

        return None

    def get_request_user():
        username = request.headers.get("X-Username")

        if not username:
            return None

        return get_user(username)

    def check_branch_access(branch):
        user = get_request_user()

        if user is None:
            return jsonify(
                {
                    "error": "authentication required"
                }
            ), 401

        if not can_access_branch(user, branch):
            return jsonify(
                {
                    "error": "forbidden",
                    "message": (
                        "user does not have access "
                        "to this branch"
                    ),
                    "branch": branch,
                }
            ), 403

        return None

    def get_authenticated_user():
        username = request.headers.get("X-Username")

        if not username:
            return None

        return get_user(username)

    def require_branch_access(branch):
        user = get_authenticated_user()

        if user is None:
            return jsonify(
                {
                    "error": "authentication required"
                }
            ), 401

        if not can_access_branch(user, branch):
            return jsonify(
                {
                    "error": "forbidden",
                    "message": (
                        "user does not have access "
                        "to this branch"
                    ),
                    "branch": branch,
                }
            ), 403

        return None

    @app.post("/api/auth/login")
    def login():
        data = request.get_json(silent=True) or {}

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify(
                {
                    "error": "username and password are required"
                }
            ), 400

        user = authenticate_user(
            username=username,
            password=password,
        )

        if user is None:
            return jsonify(
                {
                    "error": "invalid username or password"
                }
            ), 401

        return jsonify(
            {
                "authenticated": True,
                "user": user,
            }
        ), 200

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "healthy",
                "service": "MediciMess API"
            }
        ), 200

    @app.get("/api/transactions")
    def get_transactions():
        page_value = request.args.get(
            "page",
            default="1"
        )

        per_page_value = request.args.get(
            "per_page",
            default="25"
        )

        try:
            page = int(page_value)

        except ValueError:
            return jsonify(
                {
                    "error": "page must be an integer"
                }
            ), 400

        try:
            per_page = int(per_page_value)

        except ValueError:
            return jsonify(
                {
                    "error": (
                        "per_page must be an integer"
                    )
                }
            ), 400
        branch = request.args.get("branch")
        start = request.args.get("start")
        end = request.args.get("end")
        transaction_type = request.args.get("type")
        username = request.args.get("username")

        authorization_error = authorize_branch(
            username,
            branch,
        )

        if authorization_error:
            return authorization_error
        

        if page < 1:
            return jsonify(
                {
                    "error": "page must be at least 1"
                }
            ), 400

        if per_page < 1 or per_page > 100:
            return jsonify(
                {
                    "error": (
                        "per_page must be between 1 and 100"
                    )
                }
            ), 400
        try:
            start_date = (
                datetime.strptime(start, "%Y-%m-%d")
                if start
                else None
            )

            end_date = (
                datetime.strptime(end, "%Y-%m-%d")
                if end
                else None
            )

        except ValueError:
            return jsonify(
                {
                    "error": (
                        "start and end must use "
                        "YYYY-MM-DD format"
                    )
                }
            ), 400

        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            return jsonify(
                {
                    "error": (
                        "start date cannot be after end date"
                    )
                }
            ), 400    

        result = get_transaction_page(
            page=page,
            per_page=per_page,
            branch=branch,
            start=start,
            end=end,
            transaction_type=transaction_type
        )    

        return jsonify(result), 200

    @app.get("/api/kpis")
    def get_kpis():
        branch = request.args.get("branch")
        start = request.args.get("start")
        end = request.args.get("end")

        missing_parameters = []

        if not branch:
            missing_parameters.append("branch")

        if not start:
            missing_parameters.append("start")

        if not end:
            missing_parameters.append("end")

        if missing_parameters:
            return jsonify(
                {
                    "error": "missing required parameters",
                    "missing": missing_parameters
                }
            ), 400

        try:
            start_date = datetime.strptime(
                start,
                "%Y-%m-%d"
            )

            end_date = datetime.strptime(
                end,
                "%Y-%m-%d"
            )

        except ValueError:
            return jsonify(
                {
                    "error": (
                        "start and end must use "
                        "YYYY-MM-DD format"
                    )
                }
            ), 400

        if start_date > end_date:
            return jsonify(
                {
                    "error": (
                        "start date cannot be after end date"
                    )
                }
            ), 400

        result = get_kpi_summary(
            branch=branch,
            start=start,
            end=end
        )

        return jsonify(result), 200

    @app.get("/api/cashflow")
    def get_cashflow_endpoint():
        branch = request.args.get("branch")
        start = request.args.get("start")
        end = request.args.get("end")

        granularity = request.args.get(
            "granularity",
            default="monthly"
        ).casefold()

        missing_parameters = []

        if not branch:
            missing_parameters.append("branch")

        if not start:
            missing_parameters.append("start")

        if not end:
            missing_parameters.append("end")

        if missing_parameters:
            return jsonify(
                {
                    "error": "missing required parameters",
                    "missing": missing_parameters
                }
            ), 400

        allowed_granularities = [
            "daily",
            "weekly",
            "monthly"
        ]

        if granularity not in allowed_granularities:
            return jsonify(
                {
                    "error": (
                        "granularity must be daily, "
                        "weekly, or monthly"
                    )
                }
            ), 400

        try:
            start_date = datetime.strptime(
                start,
                "%Y-%m-%d"
            )

            end_date = datetime.strptime(
                end,
                "%Y-%m-%d"
            )

        except ValueError:
            return jsonify(
                {
                    "error": (
                        "start and end must use "
                        "YYYY-MM-DD format"
                    )
                }
            ), 400

        if start_date > end_date:
            return jsonify(
                {
                    "error": (
                        "start date cannot be after end date"
                    )
                }
            ), 400

        result = get_cashflow(
            branch=branch,
            start=start,
            end=end,
            granularity=granularity
        )

        return jsonify(result), 200

    @app.get("/api/loans")
    def get_loans():
        branch = request.args.get("branch")
        status = request.args.get("status")
        start = request.args.get("start")
        end = request.args.get("end")

        if not branch:
            return jsonify(
                {
                    "error": "missing required parameters",
                    "missing": ["branch"]
                }
            ), 400

        allowed_statuses = [
            "OPEN",
            "OVERDUE",
            "REPAID"
        ]

        if status:
            status = status.upper()

            if status not in allowed_statuses:
                return jsonify(
                    {
                        "error": (
                            "status must be OPEN, "
                            "OVERDUE, or REPAID"
                        )
                    }
                ), 400

        try:
            start_date = (
                datetime.strptime(start, "%Y-%m-%d")
                if start
                else None
            )

            end_date = (
                datetime.strptime(end, "%Y-%m-%d")
                if end
                else None
            )

        except ValueError:
            return jsonify(
                {
                    "error": (
                        "start and end must use "
                        "YYYY-MM-DD format"
                    )
                }
            ), 400

        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            return jsonify(
                {
                    "error": (
                        "start date cannot be after end date"
                    )
                }
            ), 400

        result = get_loan_portfolio(
        branch=branch,
        status=status,
        start=start,
        end=end,
    )

        return jsonify(result), 200

    @app.get("/api/expenses")
    def get_expenses():
        branch = request.args.get("branch")
        start = request.args.get("start")
        end = request.args.get("end")

        missing_parameters = []

        if not branch:
            missing_parameters.append("branch")

        if not start:
            missing_parameters.append("start")

        if not end:
            missing_parameters.append("end")

        if missing_parameters:
            return jsonify(
                {
                    "error": "missing required parameters",
                    "missing": missing_parameters
                }
            ), 400

        try:
            start_date = datetime.strptime(
                start,
                "%Y-%m-%d"
            )

            end_date = datetime.strptime(
                end,
                "%Y-%m-%d"
            )

        except ValueError:
            return jsonify(
                {
                    "error": (
                        "start and end must use "
                        "YYYY-MM-DD format"
                    )
                }
            ), 400

        if start_date > end_date:
            return jsonify(
                {
                    "error": (
                        "start date cannot be after end date"
                    )
                }
            ), 400

        result = get_expense_breakdown(
            branch=branch,
            start=start,
            end=end
        )

        return jsonify(result), 200

    @app.get("/api/alerts")
    def get_alert_list():
        branch = request.args.get("branch")
        start = request.args.get("start")
        end = request.args.get("end")
        severity = request.args.get("severity")

        if severity:
            severity = severity.upper()

            allowed_severities = [
                "LOW",
                "MEDIUM",
                "HIGH"
            ]

            if severity not in allowed_severities:
                return jsonify(
                    {
                        "error": (
                            "severity must be LOW, "
                            "MEDIUM, or HIGH"
                        )
                    }
                ), 400

        try:
            start_date = (
                datetime.strptime(start, "%Y-%m-%d")
                if start
                else None
            )

            end_date = (
                datetime.strptime(end, "%Y-%m-%d")
                if end
                else None
            )

        except ValueError:
            return jsonify(
                {
                    "error": (
                        "start and end must use "
                        "YYYY-MM-DD format"
                    )
                }
            ), 400

        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            return jsonify(
                {
                    "error": (
                        "start date cannot be after end date"
                    )
                }
            ), 400

        result = get_alerts(
            branch=branch,
            start=start,
            end=end,
            severity=severity
        )

        return jsonify(result), 200

    @app.post(
        "/api/alerts/<alert_id>/acknowledge"
    )
    def acknowledge_alert_endpoint(alert_id):
        request_body = request.get_json(
            silent=True
        )

        if not isinstance(request_body, dict):
            return jsonify(
                {
                    "error": (
                        "request body must be "
                        "a JSON object"
                    )
                }
            ), 400

        user_id = request_body.get("user_id")
        note = request_body.get("note")

        missing_fields = []

        if not user_id:
            missing_fields.append("user_id")

        if not note:
            missing_fields.append("note")

        if missing_fields:
            return jsonify(
                {
                    "error": "missing required fields",
                    "missing": missing_fields
                }
            ), 400

        result = acknowledge_alert(
            alert_id=alert_id,
            user_id=user_id,
            note=note
        )

        if result["outcome"] == "not_found":
            return jsonify(
                {
                    "error": "alert not found",
                    "alert_id": alert_id
                }
            ), 404

        if (
            result["outcome"]
            == "already_acknowledged"
        ):
            return jsonify(
                {
                    "error": (
                        "alert has already been "
                        "acknowledged"
                    ),
                    "alert": result["alert"]
                }
            ), 409

        return jsonify(
            {
                "message": (
                    "alert acknowledged successfully"
                ),
                "alert": result["alert"]
            }
        ), 200
    

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )