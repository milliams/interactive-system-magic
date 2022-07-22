# SPDX-FileCopyrightText: © 2022 Matt Williams <matt@milliams.com>
# SPDX-License-Identifier: MIT

import argparse
import io
import re
import shlex
import subprocess
import sys
import textwrap
from typing import Sequence

from IPython.core.magic import Magics, line_cell_magic, magics_class


def docstring(func):
    docstr = _parser(func.__name__).format_help()
    if func.__doc__ is None:
        func.__doc__ = docstr
    else:
        func.__doc__ = "\n".join([textwrap.dedent(func.__doc__), docstr])
    return func


def _parser(fn_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, prog=f"%{fn_name}")
    parser.add_argument(
        "--return",
        "-r",
        dest="do_return",
        action="store_true",
        help="Output the return code",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Call the program interactively using pexpect",
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


@magics_class
class InteractiveSystemMagics(Magics):
    def _run(self, opts: argparse.Namespace, command: Sequence[str], cell: str = None):
        if cell is None:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            print(result.stdout, end="")
            if opts.do_return:
                return result.returncode
        else:
            if opts.interactive:
                import pexpect

                d = opts.delimiter
                d_start = re.escape(d[0])
                d_end = re.escape(d[1])
                p = pexpect.spawn(shlex.join(command), encoding="utf-8")
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
                p.sendeof()
                p.expect(pexpect.EOF)
                p.wait()
                output.seek(0)
                print(output.read(), end="")
            else:
                result = subprocess.run(
                    command,
                    input=cell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                print(result.stdout, end="")
                if opts.do_return:
                    return result.returncode

    @line_cell_magic
    @docstring
    def prog(self, line: str, cell: str = None):
        """
        Run a program on the command line.
        """
        args = _parser("prog").parse_args(shlex.split(line))
        return self._run(args, args.prog + args.args, cell)

    @line_cell_magic
    @docstring
    def run_python_script(self, line: str, cell: str = None):
        """
        Run a Python script on the command line.

        Identical to ``%prog`` except it will run the passed script file to ``sys.executable``
        """
        args = _parser("run_python_script").parse_args(shlex.split(line))
        return self._run(args, [sys.executable] + args.prog + args.args, cell)


def load_ipython_extension(ipython):
    ipython.register_magics(InteractiveSystemMagics)
