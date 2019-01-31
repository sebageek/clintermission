#!/usr/bin/env python3
from clintermission import CliMenu


def main():
    q = ["Foo", "Bar", "Baz baz baz baz baz"]
    m = CliMenu(q, "Time to choose:\n")

    m.get_selection()
    print("You selected", m.get_selection())


if __name__ == '__main__':
    main()
