#!/usr/bin/env python3
from clintermission import CliMenu, CliMenuCursor, CliMenuTheme


def main():
    q = ["Foo", "Bar", "Baz baz baz baz baz"]
    m = CliMenu(q, "Time to choose:\n",
                indent=2, dedent_selection=True,
                cursor=CliMenuCursor.TRIANGLE,
                style=CliMenuTheme.BLUE)

    m.get_selection()
    print("You selected", m.get_selection())


if __name__ == '__main__':
    main()
