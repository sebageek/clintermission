#!/usr/bin/env python3
from clintermission import CliMenu, CliMenuTheme


def main():
    q = ["Foo", "Bar", "Baz baz baz baz baz"]
    m = CliMenu(q, "Time to choose:\n", style=CliMenuTheme.BOLD_HIGHLIGHT)

    if m.success:
        print("You selected", m.get_selection())
    else:
        print("You aborted the selection")


if __name__ == '__main__':
    main()
