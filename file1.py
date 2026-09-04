import pandas as pd
import time
from src.generator import generate

# Read test cases
data = pd.read_csv("test_data/requirements.csv")

results = []

for index, row in data.iterrows():

    time.sleep(5)

    tc_id = row["TC_ID"]
    requirement = row["Requirement"]

    print(f"\nRunning {tc_id}...")

    start_time = time.time()

    try:
        output = generate(requirement)

        execution_time = round(time.time() - start_time, 2)

        if output and len(str(output).strip()) > 20:
            status = "PASS"
            story_generated = "YES"
            error = ""
            print(f"{tc_id} PASSED")

        else:
            status = "FAIL"
            story_generated = "NO"
            error = "No story generated"
            print(f"{tc_id} FAILED")

    except Exception as e:

        execution_time = round(time.time() - start_time, 2)

        status = "FAIL"
        story_generated = "NO"
        error = str(e)

        print(f"{tc_id} FAILED")
        print("ERROR:", error)

    results.append(
        {
            "TC_ID": tc_id,
            "Requirement": requirement,
            "Status": status,
            "Execution_Time": execution_time,
            "Story_Generated": story_generated,
            "Error": error,
        }
    )

# Create dataframe
report = pd.DataFrame(results)

print("\n========== BENCHMARK RESULTS ==========\n")
print(report)

total = len(report)
passed = len(report[report["Status"] == "PASS"])
failed = len(report[report["Status"] == "FAIL"])

success_rate = round((passed / total) * 100, 2)

print("\n========== SUMMARY ==========")
print("Total Test Cases :", total)
print("Passed           :", passed)
print("Failed           :", failed)
print("Success Rate     :", success_rate, "%")

report.to_excel(
    "benchmark_report.xlsx",
    index=False
)

print("\nBenchmark Testing Completed")
print("Report Generated: benchmark_report.xlsx")