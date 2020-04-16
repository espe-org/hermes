#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import math
import os
import subprocess
import sys
from pathlib import Path
from shutil import which


def main():
    parser = argparse.ArgumentParser(
        "Run a binary and flags until a crash is produced, or max retries is hit"
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=0,
        help="Number of retries before giving up. 0 means unlimited",
    )
    parser.add_argument(
        "executable", type=Path, help="Path to the binary executable to be run"
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.executable.is_file():
        raise Exception("Executable isn't a file")
    rr = which("rr")
    if not which("rr"):
        raise Exception(f"rr not found on PATH: {os.environ.get('PATH', '')}")
    args.retries = args.retries or math.inf

    print(f"Running {args.retries} times using {rr}")

    @retry_while_successful(retries=args.retries)
    def chaos_mode(executable, args):
        return subprocess.check_call(
            [rr, "record", "--chaos"] + [executable] + args,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    chaos_mode(args.executable, args.args)


def retry_while_successful(retries=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal retries
            while retries > 0:
                try:
                    func(*args, **kwargs)
                    retries -= 1
                except subprocess.CalledProcessError as e:
                    print(e)
                    return
            print("All retries used")

        return wrapper

    return decorator


if __name__ == "__main__":
    main()
