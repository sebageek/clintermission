#!/usr/bin/env python3
from clintermission import CliMultiMenu, CliMenuCursor


# --- simple multiselect ---
q = [
    "Option 1",
    "Option 2",
    ("Option 3 (preselected for your convenience)", "Option 3", True),
    "Option 4"
]
m = CliMultiMenu(q, "Make your choice (<space> selects, <return> accepts):\n", cursor=CliMenuCursor.ASCII_ARROW,
                 unselected_icon="✖", selected_icon="✔")

print("You selected", m.get_selection())
print("You selected num:", m.get_selection_num())
print("You selected item:", m.get_selection_item())
