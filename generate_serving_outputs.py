import argparse
from datetime import datetime

from api.output_writer import generate_serving_outputs


def validate_date(date_value):
    try:
        datetime.strptime(
            date_value,
            "%Y-%m-%d"
        )

    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "dates must use YYYY-MM-DD format"
        ) from error

    return date_value


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate MediciMess serving-layer "
            "output files."
        )
    )

    parser.add_argument(
        "--branch",
        required=True,
        help="Branch name, such as Florence"
    )

    parser.add_argument(
        "--start",
        required=True,
        type=validate_date,
        help="Start date in YYYY-MM-DD format"
    )

    parser.add_argument(
        "--end",
        required=True,
        type=validate_date,
        help="End date in YYYY-MM-DD format"
    )

    arguments = parser.parse_args()

    if arguments.start > arguments.end:
        parser.error(
            "start date cannot be after end date"
        )

    generated_files = generate_serving_outputs(
        branch=arguments.branch,
        start=arguments.start,
        end=arguments.end
    )

    print("Generated serving-layer files:")

    for output_name, file_path in (
        generated_files.items()
    ):
        print(f"- {output_name}: {file_path}")


if __name__ == "__main__":
    main()