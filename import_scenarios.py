import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "phishsense.db"
DATASET_PATH = BASE_DIR / "data" / "scenarios_approved_for_prototype.jsonl"

REQUIRED_FIELDS = [
    "source_id",
    "sender_name",
    "sender_email",
    "subject",
    "email_body",
    "is_phishing",
    "difficulty_level",
    "explanation",
]

VALID_DIFFICULTIES = {
    "beginner",
    "intermediate",
    "advanced",
}


def load_scenarios():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    scenarios = []

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                scenario = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}"
                ) from error

            if not isinstance(scenario, dict):
                raise ValueError(
                    f"Invalid scenario on line {line_number}"
                )

            scenarios.append(scenario)

    return scenarios


def validate_scenarios(scenarios):
    errors = []
    seen_ids = set()

    for index, scenario in enumerate(scenarios, start=1):
        source_id = scenario.get("source_id")

        for field in REQUIRED_FIELDS:
            value = scenario.get(field)

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                errors.append(
                    f"Scenario {index}: Missing {field}"
                )

        if type(scenario.get("is_phishing")) is not int or (
            scenario["is_phishing"] not in (0, 1)
        ):
            errors.append(
                f"Scenario {index}: Invalid classification"
            )

        if scenario.get("difficulty_level") not in VALID_DIFFICULTIES:
            errors.append(
                f"Scenario {index}: Invalid difficulty"
            )

        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(
                f"Scenario {index}: Invalid source ID"
            )
        elif source_id in seen_ids:
            errors.append(
                f"Scenario {index}: Duplicate source ID {source_id}"
            )
        else:
            seen_ids.add(source_id)

        if scenario.get("review_status") != "approved":
            errors.append(
                f"Scenario {index}: Not approved for prototype"
            )

    return errors


def preview_scenarios(scenarios):
    print("\nPhishSense Scenario Import")
    print("=" * 45)

    phishing_count = sum(
        scenario.get("is_phishing") == 1
        for scenario in scenarios
    )

    legitimate_count = sum(
        scenario.get("is_phishing") == 0
        for scenario in scenarios
    )

    print(f"Total scenarios: {len(scenarios)}")
    print(f"Phishing: {phishing_count}")
    print(f"Legitimate: {legitimate_count}")

    print("\nScenarios:")

    for scenario in scenarios:
        print(
            f"{scenario.get('source_id')} | "
            f"{scenario.get('difficulty_level')} | "
            f"{scenario.get('subject')}"
        )

    print("\nReview statuses:")

    for status in sorted({
        str(scenario.get("review_status", "unknown"))
        for scenario in scenarios
    }):
        print(status)


def import_scenarios(scenarios):
    connection = sqlite3.connect(DATABASE_PATH)

    inserted = 0
    skipped = 0

    try:
        connection.execute("BEGIN")

        existing_ids = {
            row[0]
            for row in connection.execute(
                """
                SELECT source_id
                FROM training_scenarios
                WHERE source_id IS NOT NULL
                """
            )
        }

        for scenario in scenarios:
            source_id = scenario["source_id"]

            if source_id in existing_ids:
                skipped += 1
                continue

            connection.execute(
                """
                INSERT INTO training_scenarios (
                    sender_name,
                    sender_email,
                    subject,
                    email_body,
                    is_phishing,
                    difficulty_level,
                    explanation,
                    phishing_intent,
                    phishing_technique,
                    target_category,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario["sender_name"],
                    scenario["sender_email"],
                    scenario["subject"],
                    scenario["email_body"],
                    scenario["is_phishing"],
                    scenario["difficulty_level"],
                    scenario["explanation"],
                    scenario.get("phishing_intent"),
                    scenario.get("phishing_technique"),
                    scenario.get("target_category"),
                    source_id,
                )
            )

            existing_ids.add(source_id)
            inserted += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    print("\nDatabase Import Complete")
    print(f"New scenarios inserted: {inserted}")
    print(f"Existing scenarios skipped: {skipped}")


def main():
    scenarios = load_scenarios()

    if not scenarios:
        print("No scenarios found.")
        return

    preview_scenarios(scenarios)

    errors = validate_scenarios(scenarios)

    if errors:
        print("\nValidation errors:")

        for error in errors:
            print(error)

        print("\nImport canceled.")
        return

    print("\nStructure validation passed.")
    print("All scenarios are approved for prototype use.")

    if "--import" not in sys.argv:
        print("\nPreview only. No database changes made.")
        return

    confirmation = input(
        "\nType IMPORT to add these scenarios to SQLite: "
    )

    if confirmation != "IMPORT":
        print("Import canceled.")
        return

    import_scenarios(scenarios)


if __name__ == "__main__":
    main()