# SPDX-FileCopyrightText: © 2022 Matt Williams <matt@milliams.com>
# SPDX-License-Identifier: MIT

import argparse
import io
import re
import shlex
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from typing import List

from IPython.core.magic import Magics, line_cell_magic, magics_class


def docstring(func):
    args_docstring = _parser(func.__name__).format_help()
    standard_docstring = """
        If the magic is called in cell mode then the contents of the cell are passed to the command on its stdin.

        Using the interactive mode allows you to input on stdin in reaction to prompts in the program.
    """

    if func.__doc__ is None:
        func.__doc__ = ""
    else:
        func.__doc__ = textwrap.dedent(func.__doc__.strip("\n"))

    func.__doc__ += "\n"
    func.__doc__ += textwrap.dedent(standard_docstring.strip("\n"))
    func.__doc__ += "\n"
    func.__doc__ += textwrap.dedent(args_docstring.strip("\n"))
    return func


def _parser(fn_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, prog=f"%{fn_name}")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Call the program interactively using pexpect",
    )
    parser.add_argument(
        "--extra-args",
        default="",
        help="Extra flags to pass to the command. Useful to separate flags which are needed to amke the interactivity work, and those which are important to the reader.",
    )
    parser.add_argument("--delimiter", "-d", default="<>", help="The delimiter to use")
    if fn_name == "prog":
        prog_metavar = "PROGRAM"
        prog_help = "The program to run"
    else:
        prog_metavar = "SCRIPT"
        prog_help = "The Python script to run"
    parser.add_argument("prog", metavar=prog_metavar, nargs=1, help=prog_help)
    parser.add_argument(
        "args",
        metavar="...",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the program or script",
    )
    return parser


@dataclass
class Result:
    """
    The results and input to the system call
    """

    stdout: str
    returncode: int
    command: List[str]

    def __repr__(self):
        return self.stdout

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {}, {
            "text/x.prog": {
                "command": shlex.join(self.command),
                "returncode": self.returncode,
            }
        }


@magics_class
class InteractiveSystemMagics(Magics):
    def _run(
        self, opts: argparse.Namespace, command: List[str], cell: str = None
    ) -> Result:
        full_command = command + shlex.split(opts.extra_args)
        if cell is None:
            result = subprocess.run(
                full_command,
                input=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            return Result(result.stdout, result.returncode, command)
        else:
            if opts.interactive:
                import pexpect

                d_start = re.escape(opts.delimiter[0])
                d_end = re.escape(opts.delimiter[1])
                p = pexpect.spawn(shlex.join(full_command), encoding="utf-8")
                output = io.StringIO()
                p.logfile_read = output
                for line in cell.strip().split("\n"):
                    m = re.match(f"^{d_start}(?P<expect>.*){d_end}(?P<send>.*)$", line)
                    if m:
                        expect = m.group("expect")
                        p.expect(expect)
                        send = m.group("send")
                    else:
                        send = line
                    p.sendline(send)
                time.sleep(0.1)  # This is needed to prevent a rare race condition
                p.sendeof()
                p.expect(pexpect.EOF)
                returncode = p.wait()
                output.seek(0)
                return Result(output.read(), returncode, command)
            else:
                result = subprocess.run(
                    full_command,
                    input=cell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                )
                return Result(result.stdout, result.returncode, command)

    @line_cell_magic
    @docstring
    def prog(self, line: str, cell: str = None) -> Result:
        """
        Run a program on the command line.
        """
        args = _parser("prog").parse_args(shlex.split(line))
        return self._run(args, args.prog + args.args, cell)

    @line_cell_magic
    @docstring
    def run_python_script(self, line: str, cell: str = None) -> Result:
        """
        Run a Python script on the command line.

        Identical to ``%prog`` except it will run the passed script file to ``sys.executable``
        """
        args = _parser("run_python_script").parse_args(shlex.split(line))
        return self._run(args, [sys.executable] + args.prog + args.args, cell)


def load_ipython_extension(ipython):
    ipython.register_magics(InteractiveSystemMagics)
