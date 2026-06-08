import sys
import json
from pathlib import Path
from datetime import datetime

# Ensure project root is on sys.path so `src` imports work when running this script
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.testing.test_framework import AmmeterTestFramework


def main():
    framework = AmmeterTestFramework()
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    results = {}

    for ammeter_type in framework.get_supported_types():
        print(f"Testing {ammeter_type} ammeter...")
        results[ammeter_type] = framework.run_test(ammeter_type)

    for ammeter_type, result in results.items():
        print(f"\nResults for {ammeter_type}:")
        print(f"  port: {result['port']}")
        print(f"  command: {result['command']}")
        print(f"  status: {result['status']}")
        print(f"  final measurement: {result['measurement']} {result['unit']}")
        print(f"  raw response: {result['raw_response']}")

        print("  analysis:")
        for metric, value in result["analysis"].items():
            print(f"    {metric}: {value}")

        print("  consistency:")
        for metric, value in result["consistency"].items():
            print(f"    {metric}: {value}")

        if result.get("visualization") and result["visualization"].get("plot_file"):
            print(f"  plot saved to: {result['visualization']['plot_file']}")

    # Convert absolute paths to relative paths for portability
    for ammeter_type, result in results.items():
        if result.get("visualization") and result["visualization"].get("plot_file"):
            abs_plot = Path(result["visualization"]["plot_file"])
            rel_plot = abs_plot.relative_to(ROOT_DIR)
            result["visualization"]["plot_file"] = str(rel_plot)

    # Archive results
    results_dir = ROOT_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    archive_file = results_dir / f"{run_id}.json"
    with archive_file.open("w", encoding="utf-8") as f:
        json.dump({
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "results": results,
        }, f, indent=2)
    print(f"\n✓ Results archived to: {archive_file}")


if __name__ == "__main__":
    main()
