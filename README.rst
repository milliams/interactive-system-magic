.. SPDX-FileCopyrightText: © 2022 Matt Williams <matt@milliams.com>
   SPDX-License-Identifier: MIT

Run interactive commands with IPython/Jupyter
=============================================

Setup
-----

First, you need to load the extension with:

.. code-block:: ipython

    %load_ext interactive_system_magic

Now, you can start using it.

Running programs
----------------

If you make a code cell with:

.. code-block:: ipython

    %prog echo blah

then it will run the program ``echo blah`` and put the result in the output:

.. code-block::

    blah

So far, this is just like the ``!`` system call syntax.
However, it also allows you to send input into a program by using it in cell mode:

.. code-block:: ipython

    %%prog bc --quiet
    1+1

which will call ``bc --quiet`` (the ``--quiet`` part is to suppress the info on startup) and then pass in ``1+1`` on the stdin.
``bc`` will read this and output the result:

.. code-block::

    2

If you want to use this to demonstrate what the user would see if they ran this manually on a terminal,
i.e. to include the input as well as the output, you can use the interactive ``-i`` flag:

.. code-block:: ipython

    %%prog -i bc --quiet
    1+1

which gives:

.. code-block::

    1+1
    2

Finally, if you want to be able to respond to prompts in the program's output,
then you can use special syntax to specify the prompt you are looking for, and the thing to respond to it with.
In this case, we are calling the ``python`` program and waiting for its ``>>>`` prompt and then sending ``print("hello")``

.. code-block:: ipython

    %%prog -i -d [] python -q
    [>>> ]print("hello")

which gives:

.. code-block::

    >>> print("hello")
    hello
    >>>

Run Python scripts
------------------

As a shortcut, you can also run any Python scripts you have using the same interpreter that IPython or the Jupyter notebook is running with.
If you make a Python script with (or use an existing one of course):

.. code-block:: ipython

    %%writefile foo.py

    print("This is a script")

you can call it with:

.. code-block:: ipython

    %run_python_script foo.py

and get:

..code-block::

    This is a script

This magic supports the same cell-mode commands and interactive options as ``%%prog``.
