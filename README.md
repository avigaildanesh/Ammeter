# Ammeter Emulators

This project provides emulators for different types of ammeters: Greenlee, ENTES, and CIRCUTOR. Each ammeter emulator runs on a separate thread and can respond to current measurement requests.

## Project Structure

- `Ammeters/`
  - `main.py`: Main script to start the ammeter emulators and request current measurements.
  - `Circutor_Ammeter.py`: Emulator for the CIRCUTOR ammeter.
  - `Entes_Ammeter.py`: Emulator for the ENTES ammeter.
  - `Greenlee_Ammeter.py`: Emulator for the Greenlee ammeter.
  - `base_ammeter.py`: Base class for all ammeter emulators.
  - `client.py`: Client to request current measurements from the ammeter emulators.
- `config/`
  - `config.yaml`: Configuration file for the ammeter emulators.
- `examples/`
  - `run_tests.py`: Runner script for sample collection, analysis, and graph generation.
- `src/`
  - `testing/`
    - `AmmeterTester.py`: Class to test the ammeter emulators.
  - `utils/`
    - `config.py`: Configuration settings.
    - `logger.py`: Logging setup.
    - `Utils.py`: Utility functions, including `generate_random_float`.

## Usage

# Ammeter Emulators

## Greenlee Ammeter

- **Port**: 5000
- **Command**: `MEASURE_GREENLEE -get_measurement`
- **Measurement Logic**: Calculates current using voltage (1V - 10V) and (0.1Ω - 100Ω).
- **Measurement method** : Ohm's Law: I = V / R

## ENTES Ammeter

- **Port**: 5001
- **Command**: `MEASURE_ENTES -get_data`
- **Measurement Logic**: Calculates current using magnetic field strength (0.01T - 0.1T) and calibration factor (500 - 2000).
- **Measurement method** : Hall Effect: I = B * K

## CIRCUTOR Ammeter

- **Port**: 5002
- **Command**: `MEASURE_CIRCUTOR -get_measurement`
- **Measurement Logic**: Calculates current using voltage values (0.1V - 1.0V) over a number of samples and a random time step (0.001s - 0.01s).
- **Measurement method** : Rogowski Coil Integration: I = ∫V dt

To start the ammeter emulators and request current measurements, run the `main.py` script:
```sh
python main.py
```

## Running the tests and viewing graphs

1. Start the emulators in one terminal:
```sh
python main.py
```

2. Run the test runner in a second terminal:
```sh
python examples/run_tests.py
```

3. After the runner completes, open the generated PNG files in `reports/`:
- `reports/greenlee_measurements.png`
- `reports/entes_measurements.png`
- `reports/circutor_measurements.png`

4. Each test run is archived as JSON in `results/` with a unique run ID.

If `matplotlib` is installed, the runner saves graphs automatically. If it is not installed, the runner still prints analysis results but will not create PNG files.

## Result Archiving

The framework stores each run in `results/` as a JSON file with:
- `run_id`
- `timestamp`
- `ammeter_type`
- `sampling` parameters
- `config` values
- full `analysis` and `consistency` data
- `archive_file` path

You can retrieve historical results by using `AmmeterTestFramework.list_archived_runs()` and `AmmeterTestFramework.load_archived_run(run_id)`.
