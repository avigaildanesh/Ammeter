import json
import statistics
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..utils.config import load_config
from Ammeters.client import request_current_from_ammeter


class AmmeterTestFramework:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        self.ammeter_map = self._build_ammeter_map()
        self.root_dir = Path(__file__).resolve().parents[2]
        self.reports_dir = self.root_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.archive_dir = self.root_dir / "results"
        self.archive_dir.mkdir(exist_ok=True)

    def _build_ammeter_map(self) -> Dict[str, Dict[str, Any]]:
        ammeters = self.config.get("ammeters") or {}
        return {
            name.lower(): value
            for name, value in ammeters.items()
            if isinstance(value, dict) and value.get("port") is not None and value.get("command")
        }

    def get_supported_types(self) -> List[str]:
        return list(self.ammeter_map.keys())

    def run_test(self, ammeter_type: str) -> Dict[str, Any]:
        ammeter_type = ammeter_type.lower()
        if ammeter_type not in self.ammeter_map:
            raise ValueError(f"Unsupported ammeter type: {ammeter_type}")

        config = self.ammeter_map[ammeter_type]
        sampling = self.config.get("testing", {}).get("sampling", {})
        measurements = self._collect_samples(config, sampling)
        values = [m["value"] for m in measurements if m["value"] is not None]
        analysis = self._analyze_measurements(values)
        consistency = self._evaluate_consistency(values, analysis)
        plot_file = self._plot_measurements(ammeter_type, values)

        result = {
            "ammeter_type": ammeter_type,
            "port": config["port"],
            "command": config["command"],
            "measurements": measurements,
            "measurement": values[-1] if values else None,
            "unit": "A",
            "status": "ok" if values else "failed",
            "raw_response": measurements[-1]["raw_response"] if measurements else "",
            "analysis": analysis,
            "consistency": consistency,
            "visualization": {"plot_file": str(plot_file)} if plot_file else None,
        }

        return result

    def _collect_samples(self, config: Dict[str, Any], sampling: Dict[str, Any]) -> List[Dict[str, Any]]:
        count = int(sampling.get("measurements_count") or 1)
        frequency = sampling.get("sampling_frequency_hz")
        total_duration = sampling.get("total_duration_seconds")

        if frequency:
            interval = 1.0 / float(frequency)
        elif total_duration and count > 1:
            interval = float(total_duration) / (count - 1)
        else:
            interval = 0.0

        samples = []
        for index in range(count):
            raw_response = request_current_from_ammeter(config["port"], config["command"].encode("utf-8"), verbose=False)
            value = self._parse_response(raw_response)
            samples.append({
                "index": index + 1,
                "raw_response": raw_response,
                "value": value,
            })
            if index < count - 1 and interval > 0:
                time.sleep(interval)

        return samples

    def _parse_response(self, raw_response: str) -> Any:
        try:
            return float(raw_response)
        except (TypeError, ValueError):
            return None

    def _analyze_measurements(self, values: List[float]) -> Dict[str, Any]:
        if not values:
            return {
                "count": 0,
                "mean": None,
                "median": None,
                "standard_deviation": None,
                "minimum": None,
                "maximum": None,
            }

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "standard_deviation": statistics.stdev(values) if len(values) > 1 else 0.0,
            "minimum": min(values),
            "maximum": max(values),
        }

    def _evaluate_consistency(self, values: List[float], analysis: Dict[str, Any]) -> Dict[str, Any]:
        if not values:
            return {
                "stable": False,
                "range": None,
                "coefficient_of_variation": None,
                "remarks": "no valid measurements",
            }

        value_range = analysis["maximum"] - analysis["minimum"]
        coefficient_of_variation = (
            analysis["standard_deviation"] / analysis["mean"]
            if analysis["mean"] not in (None, 0)
            else None
        )
        stable = coefficient_of_variation is not None and coefficient_of_variation <= 0.05
        trend = self._calculate_trend(values)

        return {
            "stable": stable,
            "range": value_range,
            "coefficient_of_variation": coefficient_of_variation,
            "trend": trend,
            "remarks": "stable" if stable else "unstable",
        }

    def _generate_run_id(self) -> str:
        return f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"

    def _archive_result(self, result: Dict[str, Any], config: Dict[str, Any], sampling: Dict[str, Any]) -> Path:
        run_id = self._generate_run_id()
        archive_data = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ammeter_type": result["ammeter_type"],
            "config": config,
            "sampling": sampling,
            "result": result,
        }
        archive_file = self.archive_dir / f"{run_id}_{result['ammeter_type']}.json"
        with archive_file.open("w", encoding="utf-8") as f:
            json.dump(archive_data, f, indent=2)
        return archive_file

    def list_archived_runs(self) -> List[Dict[str, Any]]:
        runs = []
        for file_path in sorted(self.archive_dir.glob("*.json")):
            with file_path.open("r", encoding="utf-8") as f:
                archive_data = json.load(f)
            runs.append({
                "run_id": archive_data.get("run_id"),
                "timestamp": archive_data.get("timestamp"),
                "ammeter_type": archive_data.get("ammeter_type"),
                "status": archive_data.get("result", {}).get("status"),
                "archive_file": str(file_path),
            })
        return runs

    def load_archived_run(self, run_id: str) -> Dict[str, Any]:
        matches = list(self.archive_dir.glob(f"*{run_id}*.json"))
        if not matches:
            raise FileNotFoundError(f"No archived result found for run_id: {run_id}")
        with matches[0].open("r", encoding="utf-8") as f:
            return json.load(f)

    def compare_runs(self, run_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        comparison = {}
        for run_id in run_ids:
            archive_data = self.load_archived_run(run_id)
            comparison[run_id] = {
                "ammeter_type": archive_data.get("ammeter_type"),
                "timestamp": archive_data.get("timestamp"),
                "analysis": archive_data.get("result", {}).get("analysis"),
                "consistency": archive_data.get("result", {}).get("consistency"),
            }
        return comparison

    def _calculate_trend(self, values: List[float]) -> str:
        if len(values) < 2:
            return "flat"

        delta = values[-1] - values[0]
        if abs(delta) < 1e-6:
            return "flat"
        return "increasing" if delta > 0 else "decreasing"

    def _plot_measurements(self, ammeter_type: str, values: List[float]) -> Any:
        if not values:
            return None

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            return None

        plot_file = self.reports_dir / f"{ammeter_type}_measurements.png"
        plt.figure(figsize=(6, 3))
        plt.plot(range(1, len(values) + 1), values, marker="o", linestyle="-", color="blue")
        plt.title(f"{ammeter_type.capitalize()} current measurements")
        plt.xlabel("Sample #")
        plt.ylabel("Current (A)")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(plot_file)
        plt.close()

        return plot_file
