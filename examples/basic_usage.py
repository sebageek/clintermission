#!/usr/bin/env python3
from clintermission import CliMenu, CliMenuTheme, CliMenuStyle, CliMenuCursor, cli_select_item

# --- basic menu ---
q = ["Foo", "Bar", "Baz"]
m = CliMenu(q, "Time to choose:\n")

print("You selected", m.get_selection())
print()

# basic menu with an item assigned to each option and detentation of selection
q = [("Foo", 23), ("Bar", 34), ("Baz", 42)]
m = CliMenu(q, "Time to choose:\n", cursor="--->", dedent_selection=True)

print("You selected {} index {} item {}".format(m.get_selection(), m.get_selection_num(), m.get_selection_item()))
print()

# --- themes ---
q = ["Foo", "Bar", "Baz"]
m = CliMenu(q, "Time to choose:\n", style=CliMenuTheme.RED)
print("You selected", m.get_selection())
print()


# --- custom themes ---
style = CliMenuStyle(option_style='blue', highlight_style='cyan', header_style='green')
q = ["Foo", "Bar", "Baz"]
m = CliMenu(q, "Choose in style:\n", style=style)
print("You selected", m.get_selection())
print()

# --- theme defaults ---
CliMenu.set_default_cursor(CliMenuCursor.BULLET)
CliMenu.set_default_style(CliMenuTheme.BOLD_HIGHLIGHT)

q = ["Foo", "Bar", "Baz"]
m = CliMenu(q, "Time to choose:\n")

print("You selected", m.get_selection())
print()

# --- multiple headers ---
m = CliMenu()

m.add_header("Time to choose:\n", indent=False)
m.add_text("=== Category 1 ===")
m.add_option("Foo")
m.add_option("Bar")
m.add_option("Baz")
m.add_header('', indent=False)

m.add_text("=== Category 2 ===")
m.add_option("Cat 1")
m.add_option("Cat 2")
m.add_option("Cat 3")

print("You selected", m.get_selection())
print()

# --- with shortcut ---
try:
    result = cli_select_item(["Foo", "Bar", "Baz"], abort_text="Selection faiiiled!")
    print("You selected", result)
except ValueError as e:
    print(e)
print()

# --- with shortcut, shows no menu when only a single option is provided (can be disabled with return_single=False) ---
result = cli_select_item(["Single Foo"])
print("Directly selected for you as it was the only option:", result)
print()

# --- prefix/suffix ---
q = ["Foo", "Bar", "Baz"]
m = CliMenu(q, "Time to choose:\n", option_prefix=' <<<', option_suffix='>>>')
print("You selected", m.get_selection())
print()
