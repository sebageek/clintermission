# Written by Sebastian Lohff <seba@someserver.de>
# Licensed under Apache License 2.0
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, Window, HSplit
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.document import Document
from prompt_toolkit.layout.processors import Processor, Transformation


class CliMenuHeader:
    """Hold a menu header"""
    def __init__(self, text, indent=False):
        self.text = text
        self.indent = indent
        self.focusable = False


class CliMenuOption:
    """Hold a menu option"""
    def __init__(self, text, num, item=None):
        self.text = text
        self.num = num
        self.item = item
        self.focusable = True


class CliMenuCursor:
    """Collection of cursors pointing at the active menu item"""
    BULLET = '●'
    TRIANGLE = '▶'
    CLI_STAR = '*'
    CLI_ARROW = '-->'
    CLI_CAT = '=^.^='
    CAT = '😸'
    ARROW = '→'


class CliMenuStyle:
    """Style for a menu

    Allows to select header, option and selected option color
    """
    def __init__(self, option_style='', highlight_style='', header_style=''):
        self.option_style = option_style
        self.highlight_style = highlight_style
        self.header_style = header_style

        # self.option_color = '#aa0000'
        # #self.highlight_color = 'fg:ansiblue bg:ansired bold'
        # self.highlight_color = 'bold'
        # self.cursor = ' --> '
        # self.cursor = ' ● '
        # self.no_cursor = '     '
        # self.header_color = '#aa22cc'
        # self.option_indent = 4
        # self.header_indent = 4


class CliMenuTheme:
    BASIC = CliMenuStyle()
    BASIC_BOLD = CliMenuStyle(header_style='bold', highlight_style='bold')
    RED = CliMenuStyle('#aa0000', '#ee0000', '#aa0000')
    CYAN = CliMenuStyle('cyan', 'lightcyan', 'cyan')
    BLUE = CliMenuStyle('ansiblue', 'ansired', 'ansiblue')
    ANSI_CYAN = CliMenuStyle('ansicyan', 'ansibrightcyan', 'ansicyan')


class CliMenu:
    default_stye = CliMenuTheme.BASIC
    default_cursor = CliMenuCursor.TRIANGLE

    def __init__(self, options=None, header=None, cursor=None, style=None,
                 indent=2, dedent_selection=False):
        self._items = []
        self._item_num = 0
        self._ran = False
        self._success = None
        self._pos = 0
        self._option_indent = indent
        self._header_indent = indent
        self._dedent_selection = dedent_selection

        self._cursor = cursor
        if not self._cursor:
            self._cursor = self.default_cursor

        self._style = style
        if not self._style:
            self._style = self.default_stye

        if header:
            self.add_header(header)

        if options:
            for option in options:
                self.add_option(option)

    def add_header(self, title, indent=True):
        for text in title.split('\n'):
            self._items.append(CliMenuHeader(text, indent=indent))

    def add_option(self, text, item=None):
        self._items.append(CliMenuOption(text, self._item_num, item=item))
        self._item_num += 1

    def get_selection(self):
        if not self._ran:
            self._run()

        item = self._items[self._pos]

        return (item.num, item.item)

    def get_selection_num(self):
        return self.get_selection()[0]

    def get_selection_item(self):
        return self.get_selection()[1]

    def cursor(self):
        return '{} '.format(self._cursor)

    @property
    def no_cursor(self):
        # cursor with spaces minus dedent
        return ' ' * (len(self._cursor) + 1 * self._dedent_selection)

    def _transform_line(self, ti):
        style, text = list(ti.fragments)[0]
        item = self._items[ti.lineno]
        s = self._style

        # cursor
        indent = ''
        prefix = ''
        if item.focusable:
            indent += ' ' * self._option_indent

            if ti.lineno == self._pos:
                prefix += '{} '.format(self._cursor)
                style = s.highlight_style
            else:
                prefix += ' ' * (len(self._cursor) + 1 + 1 * self._dedent_selection)
                style = s.option_style
        else:
            if item.indent:
                indent += ' ' * (self._header_indent + len(self._cursor) + 1)
            style = s.header_style

        return Transformation([('', indent), (style, prefix + text)])

    def next_item(self, direction):
        if not any(item.focusable for item in self._items):
            raise RuntimeError("No focusable item found")

        while True:
            self._pos = (self._pos + direction) % len(self._items)

            # move cursor of buffer along with the selected option
            self._buf.cursor_position = self._doc.translate_row_col_to_index(self._pos, 0)

            if self._items[self._pos].focusable:
                break

    def _run(self):
        class MenuColorizer(Processor):
            def apply_transformation(_self, ti):
                return self._transform_line(ti)

        # keybindings
        self._kb = KeyBindings()

        @self._kb.add('q')
        @self._kb.add('c-c')
        def quit(event):
            event.app.exit()

        @self._kb.add('down')
        def down(event):
            self.next_item(1)

        @self._kb.add('up')
        def up(event):
            self.next_item(-1)

        @self._kb.add('right')
        @self._kb.add('c-m')
        @self._kb.add('c-space')
        def accept(event):
            self._success = True
            event.app.exit()

        text = '\n'.join(map(lambda _x: _x.text, self._items))
        self._doc = Document(text, cursor_position=self._pos)
        self._buf = Buffer(read_only=True, document=self._doc)
        self._bufctrl = BufferControl(self._buf,
                                      input_processors=[MenuColorizer()])
        split = HSplit([Window(self._bufctrl,
                               wrap_lines=True,
                               always_hide_cursor=True)])

        # set initial pos
        if not self._items[self._pos].focusable:
            self.next_item(1)

        app = Application(layout=Layout(split),
                          key_bindings=self._kb,
                          full_screen=False,
                          mouse_support=False)

        app.run()
        self._ran = True
