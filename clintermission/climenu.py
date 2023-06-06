# Written by Sebastian Lohff <seba@someserver.de>
# Licensed under Apache License 2.0
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters import is_searching
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, Window, HSplit
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit import search
from prompt_toolkit.widgets import SearchToolbar


class _CliMenuHeader:
    """Hold a menu header"""
    def __init__(self, text, indent=False, style=None):
        self.text = text
        self.indent = indent
        self.style = style
        self.focusable = False


class _CliMenuOption:
    """Hold a menu option"""
    def __init__(self, text, num, item=None, style=None, highlighted_style=None):
        self.text = text
        self.num = num
        self.item = item
        self.style = style
        self.highlighted_style = highlighted_style
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
    def __init__(self, option='', highlighted='', text='', selected=None, selected_highlighted=None):
        self.option = option
        self.highlighted = highlighted
        self.text = text
        self.selected = selected
        self.selected_highlighted = selected_highlighted


class CliSelectionStyle:
    SQUARE_BRACKETS = ('[x]', '[ ]')
    ROUND_BRACKETS = ('(x)', '( )')
    CHECKMARK = ('✔', '✖')
    THUMBS = ('👍', '👎')
    SMILEY = ('🙂', '🙁')
    SMILEY_EXTREME = ('😁', '😨')


class CliMenuTheme:
    BASIC = CliMenuStyle()
    BASIC_BOLD = CliMenuStyle(text='bold', highlighted='bold')
    RED = CliMenuStyle('#aa0000', '#ee0000', '#aa0000')
    CYAN = CliMenuStyle('cyan', 'lightcyan', 'cyan')
    BLUE = CliMenuStyle('ansiblue', 'ansired', 'ansiblue')
    ANSI_CYAN = CliMenuStyle('ansicyan', 'ansibrightcyan', 'ansicyan')
    BOLD_HIGHLIGHT = CliMenuStyle(text='bold', highlighted='bold fg:black bg:white')


class _EmptyParameter:
    pass


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
                 indent=2, dedent_selection=False, initial_pos=0,
                 option_prefix=' ', option_suffix='', right_pad_options=False):
        self._items = []
        self._item_num = 0
        self._ran = False
        self._success = None
        self._pos = 0
        self._initial_pos = initial_pos
        self._option_prefix = option_prefix
        self._option_suffix = option_suffix
        self._option_indent = indent
        self._header_indent = indent
        self._dedent_selection = dedent_selection
        self._right_pad_options = right_pad_options

        self._cursor = cursor if cursor is not None else self.default_cursor
        self._style = style if style is not None else self.default_style

        if header:
            self.add_text(header, indent=False)

        if options:
            for option in options:
                if isinstance(option, tuple):
                    self.add_option(*option)
                elif isinstance(option, dict):
                    self.add_option(**option)
                elif isinstance(option, str):
                    self.add_option(option)
                else:
                    raise ValueError("Option needs to be either tuple, dict or string, found '{}' of type {}"
                                     .format(option, type(option)))

    def add_header(self, *args, **kwargs):
        return self.add_text(*args, **kwargs)

    def add_text(self, title, indent=True, style=None):
        for text in title.split('\n'):
            self._items.append(_CliMenuHeader(text, indent=indent, style=style))

    def add_option(self, text, item=_EmptyParameter, disabled=False, style=None, highlighted_style=None):
        if disabled:
            # this is basically a text option and we just throw the item away
            self.add_text(title=text, style=style)
        else:
            if item == _EmptyParameter:
                item = text
            opt = _CliMenuOption(text, self._item_num, item=item, style=style, highlighted_style=highlighted_style)
            self._items.append(opt)
            self._item_num += 1

    @property
    def success(self):
        if not self._ran:
            self._run()

        return self._success

    def get_options(self):
        return [_item for _item in self._items if isinstance(_item, _CliMenuOption)]

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

    def _transform_prefix(self, item, lineno, prefix):
        return prefix

    def _get_style(self, item, lineno, highlighted):
        s = self._style
        if item.focusable:
            if highlighted:
                return item.highlighted_style if item.highlighted_style is not None else s.highlighted
            else:
                return item.style if item.style is not None else s.option
        else:
            return item.style if item.style is not None else s.text

    def _transform_line(self, ti):
        if len(list(ti.fragments)) == 0:
            return Transformation(ti.fragments)
        style, text = list(ti.fragments)[0]
        item = self._items[ti.lineno]
        style = self._get_style(item, ti.lineno, ti.lineno == self._pos)

        # cursor
        indent = ''
        prefix = ''
        suffix = ''
        if item.focusable:
            indent += ' ' * self._option_indent
            suffix = self._option_suffix

            if ti.lineno == self._pos:
                prefix += '{}{}'.format(self._cursor, self._option_prefix)
            else:
                prefix += ' ' * len(self._cursor) + self._option_prefix + ' ' * self._dedent_selection
        else:
            if item.indent:
                indent += ' ' * (self._header_indent + len(self._cursor) + 1)

        items = [(s if s else style, t) for s, t in ti.fragments]
        prefix = self._transform_prefix(item, ti.lineno, prefix)

        return Transformation([('', indent), (style, prefix)] + items + [(style, suffix)])

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

    def _preflight(self):
        if self._initial_pos < 0 or self._initial_pos >= self._item_num:
            raise ValueError("Initial position {} is out of range, needs to be in range of [0, {})"
                             .format(self._initial_pos, self._item_num))

        if self._right_pad_options:
            # pad all item labels with spaces to have the same length
            max_item_len = max([len(_item.text) for _item in self._items if _item.focusable])
            for item in self._items:
                if item.focusable:
                    item.text += " " * (max_item_len - len(item.text))

    def _accept(self, event):
        self._success = True
        event.app.exit()

    def _run(self):
        if self._item_num == 0:
            self._success = False
            return

        self._preflight()

        class MenuColorizer(Processor):
            def apply_transformation(_self, ti):
                return self._transform_line(ti)

        # keybindings
        self._kb = KeyBindings()

        @self._kb.add('q', filter=~is_searching)
        @self._kb.add('c-c')
        def quit(event):
            self._success = False
            event.app.exit()

        @self._kb.add('down', filter=~is_searching)
        @self._kb.add('j', filter=~is_searching)
        @self._kb.add('c-n', filter=~is_searching)
        def down(event):
            self.next_item(1)

        @self._kb.add('up', filter=~is_searching)
        @self._kb.add('k', filter=~is_searching)
        @self._kb.add('c-p', filter=~is_searching)
        def up(event):
            self.next_item(-1)

        @self._kb.add('N', filter=~is_searching)
        @self._kb.add('n', filter=~is_searching)
        def search_inc(event):
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
            self._accept(event)

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
        while not self._items[self._pos].focusable:
            self._pos += 1

        for _ in range(self._initial_pos):
            self.next_item(1)

        with create_app_session(output=create_output(always_prefer_tty=True)):
            app = Application(layout=Layout(split),
                              key_bindings=self._kb,
                              full_screen=False,
                              mouse_support=False)

            app.run()

        self._ran = True


class CliMultiMenu(CliMenu):
    default_selection_icons = CliSelectionStyle.SQUARE_BRACKETS

    @classmethod
    def set_default_selector_icons(cls, selection_icons):
        cls.default_selection_icons = selection_icons

    def __init__(self, *args, selection_icons=None, min_selection_count=0, **kwargs):
        self._multi_selected = []
        self._min_selection_count = min_selection_count
        self._selection_icons = selection_icons if selection_icons is not None else self.default_selection_icons
        super().__init__(*args, **kwargs)

    def add_option(self, text, item=_EmptyParameter, selected=False, disabled=False,
                   style=None, highlighted_style=None, selected_style=None, selected_highlighted_style=None):
        super().add_option(text, item, disabled=disabled, style=style, highlighted_style=highlighted_style)
        if disabled:
            return
        self._items[-1].selected_style = selected_style
        self._items[-1].selected_highlighted_style = selected_highlighted_style
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
        @kb.add('right', filter=~is_searching)
        def mark(event):
            if self._pos not in self._multi_selected:
                self._multi_selected.append(self._pos)
            else:
                self._multi_selected.remove(self._pos)

    def _transform_prefix(self, item, lineno, prefix):
        if item.focusable:
            if lineno in self._multi_selected:
                icon = self._selection_icons[0]
            else:
                icon = self._selection_icons[1]
            return "{}{} ".format(prefix, icon)
        else:
            return prefix

    def _get_style(self, item, lineno, highlighted):
        s = self._style
        if item.focusable and lineno in self._multi_selected:
            if highlighted:
                if item.selected_highlighted_style is not None:
                    return item.selected_highlighted_style
                if s.selected_highlighted is not None:
                    return s.selected_highlighted
            else:
                if item.selected_style is not None:
                    return item.selected_style
                if s.selected is not None:
                    return s.selected

        # no style specified or no selected state, call parent
        return super()._get_style(item, lineno, highlighted)

    def _preflight(self):
        super()._preflight()
        if self._min_selection_count > self._item_num:
            raise ValueError("A minimum of {} items was requested for successful selection but only {} exist"
                             .format(self._min_selection_count, self._item_num))

    def _accept(self, event):
        if len(self._multi_selected) >= self._min_selection_count:
            super()._accept(event)


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
