import json

from app.services.llm_service import parse_task
from app.services.providers.groq_service import GroqService

async def test_evaluation_cases():
    with open("evaluation/test_cases.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    passed = 0
    failed = 0
    llm_service = GroqService()
    for case in data["cases"]:
        case_id = case["id"]
        input_data = case["input"]
        expected = case["expected"]

        try:
            try:
                result = await parse_task(
                    request=input_data["request"],
                    reference_date=input_data["reference_date"],
                    timezone=input_data["timezone"],
                    llm_service=llm_service,
                )
            except Exception as exc:
                print(f"FAIL: {case['id']}")
                print(f"  Error: {exc}")
                continue
                                

            assert result.status == expected["status"]

            if expected["status"] == "accepted":
                assert result.task is not None

                assert result.task.title
                assert result.task.title.strip()

                assert result.task.description
                assert result.task.description.strip()

                assert result.task.priority == expected["task"]["priority"]
                assert result.task.due_date == expected["task"]["due_date"]

            else:
                assert result.task is None
                assert result.reason

            passed += 1
            print(f"PASS: {case_id}")

        except AssertionError:
            failed += 1
            print(f"FAIL: {case_id}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")

    print()
    print(f"Results: {passed}/{len(data['cases'])} passed")

    assert failed == 0

if __name__ == "__main__":
    import asyncio

    asyncio.run(test_evaluation_cases())