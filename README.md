# Python-Reverse-Shell

This project is a cross-platform reverse shell created in python3 designed to be compiled to an executable.
The executable uses the tinyaes module to compile the bytecode when using pyinstaller to prevent the shell and
server address to be decompiled and viewed.

## Disclaimer

This project was designed for educational purposes __ONLY__ and is not to be used without explicit permission.
Hacking without permission is not encouraged and the author is not responsible for any illegal use of this tool.

## Setup

install dependencies
```
$ pip install -r requirements.txt
```

## Usage

compile payload
```
$ python3 build.py [ip] [port]
```

listen on server
```
$ ncat -lp [port]
```
