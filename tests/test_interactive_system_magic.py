# SPDX-FileCopyrightText: © 2022 Matt Williams <matt@milliams.com>
# SPDX-License-Identifier: MIT

import nbformat
import pytest
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_notebook


@pytest.fixture(scope="function")
def loaded_nb():
    notebook = new_notebook()
    notebook.cells.append(new_code_cell("%load_ext interactive_system_magic"))
    nbformat.validate(notebook)
    return notebook


def execute(nb):
    nbformat.validate(nb)
    client = NotebookClient(nb)
    executed = client.execute()
    return executed


def test_load_ext(loaded_nb):
    execute(loaded_nb)


def test_simple_prog(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%prog echo blah"))

    executed = execute(loaded_nb)

    assert executed.cells[1]["outputs"][0]["text"] == "blah\n"


def test_prog_args(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%prog python --version"))

    executed = execute(loaded_nb)

    assert "Python" in executed.cells[1]["outputs"][0]["text"]


def test_cat_input(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%%prog cat\na thing"))

    executed = execute(loaded_nb)

    assert executed.cells[1]["outputs"][0]["text"] == "a thing\n"


def test_bc_input(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%%prog bc --quiet\n1+1"))

    executed = execute(loaded_nb)

    assert executed.cells[1]["outputs"][0]["text"] == "2\n"


def test_bc_input_interactive(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%%prog -i bc --quiet\n1+1"))

    executed = execute(loaded_nb)

    assert executed.cells[1]["outputs"][0]["text"] == "1+1\r\n2\r\n"


def test_cat_input_interactive(loaded_nb):
    loaded_nb.cells.append(
        new_code_cell(
            """
            %%prog -i cat
            a thing
            """
        )
    )

    executed = execute(loaded_nb)

    assert executed.cells[1]["outputs"][0]["text"] == "a thing\r\na thing\r\n"


def test_python_prompt(loaded_nb):
    loaded_nb.cells.append(
        new_code_cell(
            """
            %%prog -i -d [] python -q
            [>>> ]print(5743+7473)
            """
        )
    )

    executed = execute(loaded_nb)

    assert ">>> print(5743+7473)" in executed.cells[1]["outputs"][0]["text"]
    assert "13216" in executed.cells[1]["outputs"][0]["text"]


def test_run_python_script(loaded_nb, tmp_path):
    script = tmp_path / "a.py"
    loaded_nb.cells.append(
        new_code_cell(
            f"""
            %%writefile {script}

            import sys
            print(sys.argv)
            """
        )
    )
    loaded_nb.cells.append(new_code_cell(f"%run_python_script {script} fgf"))

    executed = execute(loaded_nb)

    assert executed.cells[2]["outputs"][0]["text"] == f"['{script}', 'fgf']\n"


def test_run_python_script_input(loaded_nb, tmp_path):
    script = tmp_path / "a.py"
    loaded_nb.cells.append(
        new_code_cell(
            f"""
            %%writefile {script}

            name = input("Enter name: ")
            print(f"Hello {{name}}")
            """
        )
    )
    loaded_nb.cells.append(
        new_code_cell(
            f"""
            %%run_python_script -i {script}
            <Enter name: >Matt
            """
        )
    )

    executed = execute(loaded_nb)

    assert (
        executed.cells[2]["outputs"][0]["text"] == "Enter name: Matt\r\nHello Matt\r\n"
    )
