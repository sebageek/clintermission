# Written by Sebastian Lohff <seba@someserver.de>
# Licensed under Apache License 2.0
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters import is_searching
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, Window, HSplit
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit import search
from prompt_toolkit.widgets import SearchToolbar


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
    ASCII_STAR = '*'
    ASCII_ARROW = '-->'
    ASCII_CAT = '=^.^='
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


class CliSelectionStyle:
    SQUARE_BRACKETS = ('[x]', '[ ]')
    ROUND_BRACKETS = ('(x)', '( )')
    CHECKMARK = ('✔', '✖')
    THUMBS = ('👍', '👎')
    SMILEY = ('🙂', '🙁')
    SMILEY_EXTREME = ('😁', '😨')


class CliMenuTheme:
    BASIC = CliMenuStyle()
    BASIC_BOLD = CliMenuStyle(header_style='bold', highlight_style='bold')
    RED = CliMenuStyle('#aa0000', '#ee0000', '#aa0000')
    CYAN = CliMenuStyle('cyan', 'lightcyan', 'cyan')
    BLUE = CliMenuStyle('ansiblue', 'ansired', 'ansiblue')
    ANSI_CYAN = CliMenuStyle('ansicyan', 'ansibrightcyan', 'ansicyan')
    BOLD_HIGHLIGHT = CliMenuStyle(header_style='bold', highlight_style='bold fg:black bg:white')


class CliMenu:
    default_style = CliMenuTheme.BASIC
    default_cursor = CliMenuCursor.TRIANGLE

    @classmethod
    def set_default_style(cls, style):
        cls.default_style = style

    @classmethod
    def set_default_cursor(cls, cursor):
        cls.default_cursor = cursor

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

        self._cursor = cursor or self.default_cursor
        self._style = style or self.default_style

        if header:
            self.add_text(header, indent=False)

        if options:
            for option in options:
                if isinstance(option, tuple):
                    self.add_option(*option)
                elif isinstance(option, dict):
                    self.add_option(**option)
                elif isinstance(option, str):
                    self.add_option(option, option)
                else:
                    raise ValueError("Option needs to be either tuple, dict or string, found '{}' of type {}"
                                     .format(option, type(option)))

    def add_header(self, *args, **kwargs):
        return self.add_text(*args, **kwargs)

    def add_text(self, title, indent=True):
        for text in title.split('\n'):
            self._items.append(CliMenuHeader(text, indent=indent))

    def add_option(self, text, item=None):
        self._items.append(CliMenuOption(text, self._item_num, item=item))
        self._item_num += 1

    @property
    def success(self):
        if not self._ran:
            self._run()

        return self._success

    def get_options(self):
        return [_item for _item in self._items if isinstance(_item, CliMenuOption)]

    @property
    def num_options(self):
        return self._item_num

    def get_selection(self):
        if self.success:
            item = self._items[self._pos]
            return (item.num, item.item)
        else:
            return (None, None)

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

    def _transform_prefix(self, item, lineno, prefix):
        return prefix

    def _transform_line(self, ti):
        if len(list(ti.fragments)) == 0:
            return Transformation(ti.fragments)
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

        items = [(s if s else style, t) for s, t in ti.fragments]
        prefix = self._transform_prefix(item, ti.lineno, prefix)

        return Transformation([('', indent), (style, prefix)] + items)

    def next_item(self, direction):
        if not any(item.focusable for item in self._items):
            raise RuntimeError("No focusable item found")

        while True:
            self._pos = (self._pos + direction) % len(self._items)

            # move cursor of buffer along with the selected option
            self._buf.cursor_position = self._doc.translate_row_col_to_index(self._pos, 0)

            if self._items[self._pos].focusable:
                break

    def sync_cursor_to_line(self, line, sync_dir=1):
        """Sync cursor to next fousable item starting on `line`"""
        assert sync_dir in (1, -1)

        self._pos = line
        while not self._items[self._pos].focusable:
            self._pos = (self._pos + sync_dir) % len(self._items)
        self._buf.cursor_position = self._doc.translate_row_col_to_index(self._pos, 0)

    def _get_search_result_lines(self):
        """Get a list of all lines that have a match with the current search result"""
        if not self._bufctrl.search_state.text:
            return []

        idx_list = []
        i = 1
        while True:
            next_idx = self._buf.get_search_position(self._bufctrl.search_state, count=i,
                                                     include_current_position=False)
            if next_idx in idx_list:
                break
            idx_list.append(next_idx)
            i += 1

        lines = []
        for idx in idx_list:
            line, _ = self._doc.translate_index_to_position(idx)
            if line not in lines:
                lines.append(line)

        return lines

    def _register_extra_kb_cbs(self, kb):
        pass

    def _run(self):
        class MenuColorizer(Processor):
            def apply_transformation(_self, ti):
                return self._transform_line(ti)

        # keybindings
        self._kb = KeyBindings()

        @self._kb.add('q', filter=~is_searching)
        @self._kb.add('c-c')
        def quit(event):
            event.app.exit()

        @self._kb.add('down', filter=~is_searching)
        @self._kb.add('j', filter=~is_searching)
        def down(event):
            self.next_item(1)

        @self._kb.add('up', filter=~is_searching)
        @self._kb.add('k', filter=~is_searching)
        def up(event):
            self.next_item(-1)

        @self._kb.add('N', filter=~is_searching)
        @self._kb.add('n', filter=~is_searching)
        def search_inc(event, filter=is_searching):
            if not self._bufctrl.search_state.text:
                return

            search_dir = 1 if event.data == 'n' else -1
            sr_lines = self._get_search_result_lines()
            if sr_lines:
                line = sr_lines[search_dir] if len(sr_lines) > 1 else sr_lines[0]
                self.sync_cursor_to_line(line, search_dir)

        @self._kb.add('c-m', filter=~is_searching)
        @self._kb.add('right', filter=~is_searching)
        def accept(event):
            self._success = True
            event.app.exit()

        @self._kb.add('c-m', filter=is_searching)
        def accept_search(event):
            search.accept_search()
            new_line, _ = self._doc.translate_index_to_position(self._buf.cursor_position)
            self.sync_cursor_to_line(new_line)

        self._register_extra_kb_cbs(self._kb)

        self._searchbar = SearchToolbar(ignore_case=True)

        text = '\n'.join(map(lambda _x: _x.text, self._items))
        self._doc = Document(text, cursor_position=self._pos)
        self._buf = Buffer(read_only=True, document=self._doc)
        self._bufctrl = BufferControl(self._buf,
                                      search_buffer_control=self._searchbar.control,
                                      preview_search=True,
                                      input_processors=[MenuColorizer()])
        split = HSplit([Window(self._bufctrl,
                               wrap_lines=True,
                               always_hide_cursor=True),
                        self._searchbar])

        # set initial pos
        self.sync_cursor_to_line(0)

        app = Application(layout=Layout(split),
                          key_bindings=self._kb,
                          full_screen=False,
                          mouse_support=False)

        app.run()
        self._ran = True


class CliMultiMenu(CliMenu):
    default_selected_icon = '[x]'
    default_unselected_icon = '[ ]'

    @classmethod
    def set_default_selector_icons(cls, selected_icon, unselected_icon):
        cls.default_selected_icon = selected_icon
        cls.default_unselected_icon = unselected_icon

    def __init__(self, *args, selected_icon=None, unselected_icon=None, **kwargs):
        self._multi_selected = []
        self._selected_icon = selected_icon or self.default_selected_icon
        self._unselected_icon = unselected_icon or self.default_unselected_icon
        super().__init__(*args, **kwargs)

    def add_option(self, text, item=None, selected=False):
        super().add_option(text, item)
        if selected:
            self._multi_selected.append(len(self._items) - 1)

    def get_selection(self):
        if self.success:
            return [(self._items[n].num, self._items[n].item) for n in self._multi_selected]
        else:
            return None

    def get_selection_num(self):
        if self.success:
            return [self._items[n].num for n in self._multi_selected]
        else:
            return None

    def get_selection_item(self):
        if self.success:
            return [self._items[n].item for n in self._multi_selected]
        else:
            return None

    def _register_extra_kb_cbs(self, kb):
        @kb.add('space', filter=~is_searching)
        def mark(event):
            if self._pos not in self._multi_selected:
                self._multi_selected.append(self._pos)
            else:
                self._multi_selected.remove(self._pos)

    def _transform_prefix(self, item, lineno, prefix):
        if item.focusable:
            if lineno in self._multi_selected:
                icon = self._selected_icon
            else:
                icon = self._unselected_icon
            return "{}{} ".format(prefix, icon)
        else:
            return prefix


def cli_select_item(options, header=None, abort_exc=ValueError, abort_text="Selection aborted.", style=None,
                    return_single=True):
    """Helper function to quickly get a selection with just a few arguments"""
    menu = CliMenu(header=header, options=options, style=style)

    if return_single and menu.num_options == 1:
        item = menu.get_options()[0]
        return item.num, item.item

    if not menu.success:
        raise abort_exc(abort_text)

    return menu.get_selection()
