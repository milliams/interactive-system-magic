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


def get_execute_result(cell):
    return next(
        o for o in cell.get("outputs", []) if o.get("output_type") == "execute_result"
    )


def get_text_output(cell):
    return get_execute_result(cell)["data"]["text/plain"]


def get_metadata(cell):
    return get_execute_result(cell)["metadata"]["text/x.prog"]


def test_load_ext(loaded_nb):
    execute(loaded_nb)


def test_simple_prog(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%prog echo blah"))

    executed = execute(loaded_nb)

    assert get_text_output(executed.cells[1]) == "blah"
    assert get_metadata(executed.cells[1])["returncode"] == 0


def test_prog_args(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%prog python --version"))

    executed = execute(loaded_nb)

    assert "Python" in get_text_output(executed.cells[1])


def test_cat_input(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%%prog cat\na thing"))

    executed = execute(loaded_nb)

    assert get_text_output(executed.cells[1]) == "a thing"


def test_bc_input(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%%prog bc --quiet\n1+1"))

    executed = execute(loaded_nb)

    assert get_text_output(executed.cells[1]) == "2"


def test_bc_input_interactive(loaded_nb):
    loaded_nb.cells.append(new_code_cell("%%prog -i bc --quiet\n1+1"))

    executed = execute(loaded_nb)

    assert get_text_output(executed.cells[1]) == "1+1\n2"


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

    assert get_text_output(executed.cells[1]) == "a thing\na thing"


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

    assert ">>> print(5743+7473)" in get_text_output(executed.cells[1])
    assert "13216" in get_text_output(executed.cells[1])


def test_ipython_prompt(loaded_nb):
    loaded_nb.cells.append(
        new_code_cell(
            """
            %%prog ipython --colors=NoColor --no-confirm-exit --no-banner --simple-prompt
            5743+7473
            """
        )
    )

    executed = execute(loaded_nb)

    assert "13216" in get_text_output(executed.cells[1])


def test_ipython_prompt_interactive(loaded_nb):
    loaded_nb.cells.append(
        new_code_cell(
            r"""
            %%prog -i -d <> ipython --colors=NoColor --no-confirm-exit --no-banner --simple-prompt
            <In \[\d]: >a = 5743
            <In \[\d]: >b = 7473
            <In \[\d]: >a + b
            """
        )
    )

    executed = execute(loaded_nb)

    assert "13216" in get_text_output(executed.cells[1])


def test_ipython_prompt_interactive_extra_args(loaded_nb):
    loaded_nb.cells.append(
        new_code_cell(
            r"""
            %%prog -i -d <> --extra-args="--colors=NoColor --no-confirm-exit --no-banner --simple-prompt" ipython
            <In \[\d]: >a = 5743
            <In \[\d]: >b = 7473
            <In \[\d]: >a + b
            """
        )
    )

    executed = execute(loaded_nb)

    assert "13216" in get_text_output(executed.cells[1])


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

    assert get_text_output(executed.cells[2]) == f"['{script}', 'fgf']"


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

    assert get_text_output(executed.cells[2]) == "Enter name: Matt\nHello Matt"
