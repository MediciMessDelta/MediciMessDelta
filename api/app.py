from datetime import datetime

from flask import Flask, jsonify, request

from api.data_service import get_transaction_page
from api.kpi_service import get_kpi_summary


def create_app():
    app = Flask(__name__)

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
        page = request.args.get(
            "page",
            default=1,
            type=int
        )

        per_page = request.args.get(
            "per_page",
            default=25,
            type=int
        )
        branch = request.args.get("branch")
        start = request.args.get("start")
        end = request.args.get("end")
        transaction_type = request.args.get("type")
        

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
    

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )