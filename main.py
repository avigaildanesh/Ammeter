import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.client import request_current_from_ammeter


def run_greenlee_emulator():
    greenlee = GreenleeAmmeter(5000)
    greenlee.start_server()

def run_entes_emulator():
    entes = EntesAmmeter(5001)
    entes.start_server()

def run_circutor_emulator():
    circutor = CircutorAmmeter(5002)
    circutor.start_server()

if __name__ == "__main__":
    # Start each ammeter in a separate thread (non-daemon so they keep running)
    threading.Thread(target=run_greenlee_emulator).start()
    threading.Thread(target=run_entes_emulator).start()
    threading.Thread(target=run_circutor_emulator).start()

    print("Ammeter emulators started on ports 5000, 5001, 5002. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down emulators.")
