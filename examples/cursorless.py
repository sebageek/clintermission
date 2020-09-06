#!/usr/bin/env python3
from clintermission import CliMenu, CliMenuTheme


q = ["Foo", "Bar", "Baz baz baz baz baz"]
m = CliMenu(q, "Time to choose:\n", style=CliMenuTheme.BOLD_HIGHLIGHT,
            cursor='', option_prefix=' ', option_suffix=' ', right_pad_options=True)
m.get_selection()
print("You selected", m.get_selection())
