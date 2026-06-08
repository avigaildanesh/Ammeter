from socket import socket, AF_INET, SOCK_STREAM


def request_current_from_ammeter(port: int, command: bytes, verbose: bool = True) -> str:
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(('localhost', port))
        s.sendall(command)
        data = s.recv(1024)
        response = data.decode('utf-8') if data else ""
        if verbose:
            if response:
                print(f"Received current measurement from port {port}: {response} A")
            else:
                print("No data received.")
        return response

