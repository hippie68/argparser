"""An enjoyable argument parser module that follows common conventions."""

import sys
from shutil import get_terminal_size
from typing import Callable

MAX_COLUMNS = get_terminal_size()[0]
MAX_LINE_LENGTH = 80 if MAX_COLUMNS > 80 else MAX_COLUMNS
MIN_DESCRIPTION_WIDTH = int(MAX_LINE_LENGTH // 1.618)


class ParsingError(Exception):
    """Raising this exception causes parsing to stop."""


class Option:
    """Data that specifies one of a command's options.

    Args:
        short_name: A single unique character (without leading "-").
        long_name: A longer name (without leading "--").
        arg: Specifies if and how the option accepts an argument, by
            employing the following rules and common command-line
            interface conventions:
            - If arg is a non-empty string (the argument's name), the
              option will accept an argument.
            - If arg is enclosed in brackets ("[...]"), the argument
              will be treated as optional. On the command line it can
              only be passed by attaching it either directly to a short
              option ("-oARG") or via an equals sign to a long option
              ("--option=ARG").
            - If arg is not enclosed in brackets, the argument is
              treated as mandatory. It can either be attached to the
              option as described above or follow it as a separate
              command-line argument ("-o ARG" or "--option ARG").
        description: The option's full manual that will be displayed
            as part of the print_help() function's output.
        callback: A callable (function, lambda) that is run
            automatically when a Command's parse() method encounters the
            option. If an option-argument is present, it will be used as
            the callable's argument.
        hidden: Options that are hidden won't appear in the help output.
    """

    def __init__(
        self,
        short_name: str,
        long_name: str,
        arg: str,
        description: str,
        callback: Callable[[str], None],
        hidden: bool = False,
    ):
        self.short_name = short_name
        self.long_name = long_name
        self.arg = arg
        self.description = description
        self.callback = callback
        self.hidden = hidden


class Command:
    """Class containing rules that determine how to interprete command-line arguments.

    Args:
        usage: A string that describes how to call the command in a
            nutshell. There is no strict convention, but the following
            rules should be adhered: Operands enclosed in brackets
            ("[]") are optional. Ellipses ("...") indicate that an
            operand may be repeated. Operands that are enclosed in angle
            brackets ("<>") or not enclosed at all are mandatory.
        manual:
            The command's detailed description, ideally which leaves no
            room for questions or misinterpretation.
        options:
            A list of Option objects (see class Option) which represent
            the command's options.
    """

    def __init__(
        self,
        name: str,
        usage: str = None,
        manual: str = None,
        options: list[Option] = [],
    ):
        self.name = name
        self.usage = usage
        self.manual = manual
        self.options = options

    def _parse(self) -> bool:
        """Parse the next command-line argument.

        Returns:
            True unless there is no next command-line argument.

        Raises:
            ParsingError: The command-line arguments contain an error.
        """

        if self.argv_index > self.argc - 1:
            return False

        arg = self.argv[self.argv_index]
        arg_len = len(arg)

        if arg_len == 0:
            self.operands.append(arg)
        elif arg == "--":  # End of options.
            self.argv_index += 1
            while self.argv_index < self.argc:
                self.operands.append(self.argv[self.argv_index])
                self.argv_index += 1
            return False
        elif arg[0] == "-":
            if arg_len == 1:
                self.operands.append(arg)
            elif arg[1] == "-":  # Long option.
                long_name = arg[2:]
                oarg = None
                oarg_pos = long_name.find("=")
                if oarg_pos != -1:
                    oarg = long_name[oarg_pos + 1 :]
                    long_name = long_name[:oarg_pos]

                for option in self.options:
                    if option.long_name == long_name:
                        if oarg is not None:
                            if not option.arg:
                                raise ParsingError(
                                    f"Option --{long_name} does not allow an argument."
                                )
                        elif option.arg and not option.arg.startswith("["):
                            self.argv_index += 1
                            if self.argv_index > self.argc - 1:
                                raise ParsingError(
                                    f"Option --{long_name} requires an argument."
                                )
                            else:
                                oarg = self.argv[self.argv_index]

                        if option.callback:
                            if option.arg:
                                option.callback(oarg)
                            else:
                                option.callback()

                        break
                else:
                    raise ParsingError(f"Unknown option: --{long_name}")
            else:  # Short option.
                short_name = arg[1]
                oarg = None
                for option in self.options:
                    if option.short_name == short_name:
                        if option.arg:
                            if arg_len > 2:
                                oarg = arg[2:]
                            elif not option.arg.startswith("["):
                                self.argv_index += 1
                                if self.argv_index > self.argc - 1:
                                    raise ParsingError(
                                        f"Option -{short_name} requires an argument."
                                    )
                                oarg = self.argv[self.argv_index]

                        if option.callback:
                            if option.arg:
                                option.callback(oarg)
                            else:
                                option.callback()

                        break
                else:
                    raise ParsingError(f"Unknown option: -{short_name}")

                if not oarg and len(arg) > 2:  # Short option block (-abc).
                    self.argv[self.argv_index] = "-" + arg[2:]
                    return True

        else:
            self.operands.append(arg)

        self.argv_index += 1
        return True

    def parse(self, argv: list[str]):
        """Parse a list of command-line arguments, taking action as
        specified in the Command's list of Options.

        Args:
            argv: The list of command-line arguments. The first argument
                argv[0] is expected to be the command's name.

        Returns:
            True on error, otherwise False.
        """

        self.operands = []
        self.argv = argv.copy()
        self.argc = len(argv)
        self.argv_index = 1

        try:
            while self._parse():
                pass
        except ParsingError as e:
            print(str(e), file=sys.stderr)
            return True
        else:
            return False


def print_help(cmd: Command, file=sys.stdout):
    """Generate and print a formatted help screen text that contains
    a specific command's usage information, including its options.

    Args:
        cmd: The Command whose help screen is to be printed.
        output_file: The output's destination.
    """

    def create_option_usage(option: Option) -> str:
        """Create the "usage" part without the option's description."""
        s = "  "
        if option.short_name:
            s += f"-{option.short_name}"
            if not option.long_name:
                if option.arg:
                    if option.arg.startswith("["):
                        s += option.arg
                    else:
                        s += f" {option.arg}"
            else:
                s += ", "
        else:
            s += "    "

        if option.long_name:
            s += f"--{option.long_name}"
            if option.arg:
                if option.arg.startswith("["):
                    s += f"[={option.arg[1:]}"
                else:
                    s += f" {option.arg}"
        s += "  "
        return s

    def create_option_usages(cmd: Command) -> tuple[str, str]:
        option_usages = []
        for option in cmd.options:
            if option.hidden:
                continue
            option_usages.append((create_option_usage(option), option.description))
        option_usages.sort(key=lambda usage: str.casefold(usage[0]))
        return option_usages

    def print_block(string: str, start_col: int, indent: int, file):
        """Print a string in the form of a word-wrapped, indented text block.

        Args:
            string: The string.
            start_col: The cursor's known current column.
            indent: The desired indentation width for wrapped lines.
            file: The output's destination.
        """

        def get_indent(s: str) -> int:
            indent = 0
            bullet_point = False
            s_len = len(s)
            while indent < s_len:
                if not bullet_point and s[indent] in "-*":
                    if indent + 1 < s_len and s[indent + 1] == " ":
                        bullet_point = True
                elif s[indent] != " ":
                    break
                indent += 1
            return indent

        def next_word_len(s: str) -> int:
            ignore_spaces = False
            s_len = len(s)
            for i in range(s_len):
                if s[i] == " ":
                    if ignore_spaces:
                        return i
                else:
                    ignore_spaces = True

                if s[i] == "\n":
                    if i == 0:
                        return 1
                    else:
                        return i
            return s_len

        col = start_col

        if start_col > indent:
            start_col = indent

        linebreak_encountered = False
        indentation = 0  # Indentation width found in the string.

        while True:
            word_len = next_word_len(string)
            if word_len == 0:
                break

            if string[0] == "\n":
                print(file=file)
                col = 0
                string = string[1:]
                linebreak_encountered = True
                indentation = 0
                continue

            if col == 0:
                col = start_col
                print(" " * col, end="", file=file)
                if indentation:
                    print(" " * (indentation), end="", file=file)
                    col += indentation
                if string[0] == " ":
                    if linebreak_encountered:
                        indentation = get_indent(string)
                    else:
                        string = string[1:]
                        continue
                linebreak_encountered = False

            remaining_cols = MAX_LINE_LENGTH - col
            if word_len > remaining_cols:
                if col == start_col or (indentation and col == start_col + indentation):
                    print(string[:remaining_cols], end="", file=file)
                    string = string[remaining_cols:]
                print(file=file)
                col = 0
                continue

            print(string[:word_len], end="", file=file)
            string = string[word_len:]
            col += word_len
        print(file=file)

    print(f"Usage: {cmd.name} {cmd.usage}", file=file)
    if cmd.manual:
        print_block(f"\n{cmd.manual}", 0, 0, file)

    if cmd.options:
        print("\nOptions:", file=file)

        option_usages = create_option_usages(cmd)
        longest = len(max(option_usages, key=lambda o: len(o[0]))[0])
        if MAX_LINE_LENGTH - longest < MIN_DESCRIPTION_WIDTH:
            longest = MAX_LINE_LENGTH - MIN_DESCRIPTION_WIDTH

        for option in option_usages:
            usage_string = option[0] + " " * (longest - len(option[0]))
            print(usage_string, end="", file=file)
            print_block(
                option[1],
                len(usage_string),
                longest,
                file,
            )
