"""Example program for the argparser module."""

import sys

import argparser


def convert_number(arg: str) -> int:
    """Companion function for option -n."""
    try:
        number = int(arg)
    except ValueError:
        raise argparser.ParsingError(f"Not a number: {number}.")

    if number < 10 or number > 20:
        raise argparser.ParsingError(
            f"Number out of range: {number} (allowed range: 10-20)."
        )

    return number


# Dictionary that stores the program's settings.
settings = {
    "verbose_flag": False,
    "filename": None,
    "log_enabled": False,
    "log_file": "log.txt",
    "n": 10,
}

cmd = argparser.Command(
    "main.py",
    "[OPTION...] OPERAND...",
    "This is a test program that uses the argparser module to show how to implement"
    " different options. Notice how the help screen properly word-wraps the text.\n\n"
    "This includes newline characters and indentation:\n\n"
    "   - As you can see, indentation entered on purpose...\n"
    "   - ...is being respected.\n"
    "\nThank you for trying this out.",
    [
        argparser.Option(
            "v",
            "verbose",
            None,
            "Enable verbose program output.",
            # To modify variables, settattr() can be used.
            lambda: settings.update({"verbose_flag": True}),
        ),
        argparser.Option(
            "f",
            "file",
            "FILENAME",  # The option requires an option-argument...
            "Write output to file FILENAME.",
            # ... which the parser passes to the callback, expecting a callable that
            # processes a single parameter.
            lambda arg: settings.update({"filename": arg}),
        ),
        argparser.Option(
            short_name="h",
            long_name="help",
            arg=None,
            description="Print help screen and quit.",
            # To implement the "and quit", a tuple can be used to chain the commands.
            callback=lambda: (argparser.print_help(cmd), sys.exit(0)),
        ),
        argparser.Option(
            "l",
            "log",
            "[LOG_FILE]",
            f"Enable loggging (default log file: {settings['log_file']}).",
            lambda arg: (
                settings.update({"log_enabled": True}),
                # Optional option-arguments are None by default, which can be utilized
                # by short-circuiting Boolean operators.
                arg is not None and settings.update({"log_file": arg}),
            ),
        ),
        argparser.Option(
            "n",
            None,
            "NUMBER",
            "Set n to a NUMBER between 10 and 20.",
            # Here we use a dedicated function to handle ValueError exceptions and
            # perform range checking.
            lambda arg: settings.update({"n": convert_number(arg)}),
        ),
    ],
)

print("Program settings before parsing:")
print(settings, end="\n\n")

if cmd.parse(sys.argv):
    print("Parsing failed.")
else:
    print("Parsing successful.")

print("\nProgram settings after parsing:")
print(settings)

# All remaining operands (non-options) are stored in cmd.operands:
print(f"\nRemaining operands: {cmd.operands}")
