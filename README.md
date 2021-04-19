# duplicate-crash-identifier
This repository contains our implementation for "[K-Detector: Identifying Duplicate Crash Failures in Large-Scale Software Delivery](https://ieeexplore.ieee.org/document/9307721)", which is nominated as candidate to the **Best Industry Paper Award** in the 31st International Symposium on Software Reliability Engineering:
![](https://raw.githubusercontent.com/snlndod/mPOST/master/KDetector/00.png)

Its core mathematical model is protected by U.S. Patent:
![](https://raw.githubusercontent.com/snlndod/mPOST/master/KDetector/01.png)

## Install
There are some dependencies that need to be installed in advance.

### LLVM
Install [Clang](http://releases.llvm.org/download.html) using pre-built binary:
```bash
$ wget https://github.com/llvm/llvm-project/releases/download/llvmorg-11.0.0/clang+llvm-11.0.0-x86_64-linux-sles12.4.tar.xz
$ sudo tar -C /usr/local -xvf clang+llvm-11.0.0-x86_64-linux-sles12.4.tar.xz --strip 1
```

Verify that Clang has installed successfully:
```bash
$ clang --version
clang version 11.0.0
Target: x86_64-unknown-linux-gnu
Thread model: posix
InstalledDir: /usr/local/bin
```

### MongoDB
Import the MongoDB public key:
```bash
$ sudo rpm --import https://www.mongodb.org/static/pgp/server-4.4.asc
```

Add the MongoDB repository:
```bash
$ sudo zypper addrepo --gpgcheck "https://repo.mongodb.org/zypper/suse/15/mongodb-org/4.4/x86_64/" mongodb
```

Install the MongoDB packages:
```bash
$ sudo zypper -n install mongodb-org
```

Start MongoDB:
```bash
$ sudo systemctl start mongod
```

Verify that MongoDB has started successfully:
```bash
$ sudo systemctl status mongod
Nov 24 02:38:37 i516697 systemd[1]: Starting MongoDB Database Server...
Nov 24 02:38:37 i516697 mongod[48038]: about to fork child process, waiting until server is ready for connections.
Nov 24 02:38:37 i516697 mongod[48038]: forked process: 48040
Nov 24 02:38:38 i516697 mongod[48038]: child process started successfully, parent exiting
Nov 24 02:38:38 i516697 systemd[1]: Started MongoDB Database Server.
```

Begin using MongoDB:
```bash
$ mongo
```

### Python
Install the required packages:
```bash
$ pip install -r requirements.txt
```

In addition, we build abstract syntax tree using Python bindings for libclang:
![](https://raw.githubusercontent.com/snlndod/mPOST/master/KDetector/02.png)

## Usage
We provide 4 main features:
- Crawling recent crash dumps which contains knowledge updating:
    ```bash
    $ ./src/main.py --crawl
    ```
- Training for parameter tuning which contains data sampling:
    ```bash
    $ ./src/main.py --train
    ```
- Count file names (i.e., stop words) that can be filtered:
    ```bash
    $ ./src/main.py --stop
    ```
- Detect crash similarity through the mathematical model:
    ```bash
    $ ./src/main.py --detect [<crash_dumps>]
    ```

## Evaluation
We evaluate our code on a development server:
- SLES15 SP1;
- 40 CPUs;
- 160 GB RAM;
- 1 TB Disk;

The elapsed time in seconds:
|Crawl|Train|Stop|Detect|
|:-:|:-:|:-:|:-:|
|775.94|158.47|621.78|5.59|

## Contributing
We love contributions! Before submitting a Pull Request, it's always good to start with a new issue first.

## License
This repository is licensed under Apache 2.0. Full license text is available in [LICENSE](https://github.com/SAP/duplicate-crash-identifier/blob/main/LICENSE).

Detailed information including third-party components and their licensing/copyright information is available via [REUSE](https://api.reuse.software/info/github.com/SAP/duplicate-crash-identifier).
