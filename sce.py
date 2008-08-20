#!/usr/bin/python2.5


import curses
import codecs
import locale
import os
import os.path
import subprocess
import sys
import traceback


class Scroll :
	
	def __init__ (self) :
		self._lines = [u'']
	
	def is_empty (self) :
		return len (self._lines) == 0
	
	def get_length (self) :
		return len (self._lines)
	
	def select (self, _index) :
		return self._lines[_index]
	
	def update (self, _index, _string) :
		self._lines.add (unicode (_string))
	
	def append (self, _string) :
		if (len (self._lines) == 1) and (len (self._lines[0]) == 0) :
			self._lines[0] = _string
		else :
			self._lines.append (unicode (_string))
	
	def include_before (self, _index, _string) :
		self._lines.insert (_index, unicode (_string))
	
	def include_after (self, _index, _string) :
		self._lines.insert (_index + 1, unicode (_string))
	
	def exclude (self, _index) :
		del self._lines[_index]
		if len (self._lines) == 0 :
			self._lines = [u'']
	
	def empty (self) :
		self._lines = [u'']
	
	def split (self, _index, _column) :
		if (_column == 0) :
			self._lines.insert (_index, u'')
		else :
			_line = self._lines[_index]
			self._lines[_index] = _line[: _column]
			self._lines.insert (_index + 1, _line[_column :])
	
	def unsplit (self, _index) :
		_line_0 = self._lines[_index]
		_line_1 = self._lines[_index + 1]
		_line = _line_0 + _line_1
		del self._lines[_index + 1]
		self._lines[_index] = _line
	
	def insert (self, _index, _column, _string) :
		_line = self._lines[_index]
		if (_column == 0) :
			_line = unicode (_string) + _line
		elif (_column < len (_line)) :
			_line = _line[: _column] + unicode (_string) + _line[_column :]
		elif (_column == len (_line)) :
			_line = _line + unicode (_string)
		else :
			_line = _line + (' ' * (_column - len (_line))) + unicode (_string)
		self._lines[_index] = _line
	
	def delete (self, _index, _column, _length) :
		_line = self._lines[_index]
		if (_column > len (_line)) :
			pass
		elif (_column + _length) >= len (_line) :
			_line = _line[: _column]
		elif _column == 0 :
			_line = _line[_length :]
		else :
			_line = _line[: _column] + _line[_column + _length :]
		self._lines[_index] = _line
	
	def select_real_column (self, _index, _column) :
		return self.compute_real_column (self._lines[_index], _column)
	
	def select_visual_column (self, _index, _column) :
		return self.compute_visual_column (self._lines[_index], _column)
	
	def select_visual_length (self, _index) :
		return self.compute_visual_length (self._lines[_index])
	
	def compute_real_column (self, _string, _column) :
		_index = 0
		_length = 0
		for _character in _string :
			_code = ord (_character)
			if _code == 9 :
				_length = ((_length / 4) + 1) * 4
			else :
				_length += 1
			if _length > _column :
				break
			_index += 1
		if _length < _column :
			_index += _column - _length
		return _index
	
	def compute_visual_column (self, _string, _column) :
		_index = 0
		_length = 0
		for _character in _string :
			_code = ord (_character)
			if _index == _column :
				break
			if _code == 9 :
				_length = ((_length / 4) + 1) * 4
			else :
				_length += 1
			_index += 1
		if _index < _column :
			_length += _column - _index
		return _length
	
	def compute_visual_length (self, _string) :
		_length = 0
		for _character in _string :
			_code = ord (_character)
			if _code == 9 :
				_length = ((_length / 4) + 1) * 4
			else :
				_length += 1
		return _length
#


class Mark :
	
	def __init__ (self) :
		self._line = 0
		self._column = 0
	
	def get_line (self) :
		return self._line
	
	def get_column (self) :
		return self._column
	
	def set_line (self, _line) :
		self._line = _line
	
	def set_column (self, _column) :
		self._column = _column
	
	def increment_line (self, _increment) :
		self._line += _increment
	
	def increment_column (self, _increment) :
		self._column += _increment
	
	def correct (self) :
		pass
#


class ViewMark (Mark) :
	
	def __init__ (self, _view) :
		Mark.__init__ (self)
		self._view = _view
	
	def correct (self) :
		self._view.correct_marks ()
#


class View :
	
	def __init__ (self, _scroll) :
		self._scroll = _scroll
		self._cursor = ViewMark (self)
		self._head = ViewMark (self)
		self._tail = ViewMark (self)
		self._mark = ViewMark (self)
		self._mark_enabled = False
		self._max_lines = 25
		self._max_columns = 80
	
	def get_scroll (self) :
		return self._scroll
	
	def get_cursor (self) :
		return self._cursor
	
	def get_head (self) :
		return self._head
	
	def get_tail (self) :
		return self._tail
	
	def get_mark (self) :
		return self._mark
	
	def is_mark_enabled (self) :
		return self._mark_enabled
	
	def set_mark_enabled (self, _enabled) :
		self._mark_enabled = _enabled
	
	def set_max (self, _lines, _columns) :
		self._max_lines = _lines
		self._max_columns = _columns
	
	def correct_marks (self) :
		
		_cursor_line = self._cursor._line
		_cursor_column = self._cursor._column
		_head_line = self._head._line
		_head_column = self._head._column
		_tail_line = self._tail._line
		_tail_column = self._tail._column
		_max_lines = self._max_lines
		_max_columns = self._max_columns
		_mark_line = self._mark._line
		_mark_column = self._mark._column
		_scroll_lines = self._scroll.get_length ()
		
		if _cursor_line < 0 :
			_cursor_line = 0
		elif _cursor_line >= _scroll_lines :
			_cursor_line = _scroll_lines - 1
		if _cursor_column < 0 :
			_cursor_column = 0
		
		if _mark_line < 0 :
			_mark_line = 0
		elif _mark_line >= _scroll_lines :
			_mark_line = _scroll_lines - 1
		if _mark_column < 0 :
			_mark_column = 0
		
		if _scroll_lines <= _max_lines :
			_head_line = 0
			_tail_line = _scroll_lines - 1
		else :
			if _cursor_line <= (_head_line + 5) :
				_head_line = _cursor_line - 5
				if _head_line < 0 :
					_head_line = 0
				_tail_line = _head_line + _max_lines - 1
			if _cursor_line >= (_tail_line - 5) :
				_tail_line = _cursor_line + 5
				if _tail_line >= _scroll_lines :
					_tail_line = _scroll_lines - 1
				_head_line = _tail_line - _max_lines + 1
		
		if _tail_column - _head_column < _max_columns :
			_tail_column = _head_column + _max_columns - 1
		if _cursor_column <= (_head_column + 10) :
			_head_column = _cursor_column - 10
			if _head_column < 0 :
				_head_column = 0
			_tail_column = _head_column + _max_columns - 1
		if _cursor_column >= (_tail_column - 10) :
			_tail_column = _cursor_column + 10
			_head_column = _tail_column - _max_columns + 1
		
		self._cursor._line = _cursor_line
		self._cursor._column = _cursor_column
		self._head._line = _head_line
		self._head._column = _head_column
		self._tail._line = _tail_line
		self._tail._column = _tail_column
		self._mark._line = _mark_line
		self._mark._column = _mark_column
#


class Shell :
	
	def __init__ (self, _view, _handler) :
		self._view = _view
		self._handler = _handler
	
	def get_view (self) :
		return self._view
	
	def get_handler (self) :
		return self._key_handler
	
	def open (self) :
		
		locale.setlocale (locale.LC_ALL,'')
		
		self._window = curses.initscr ()
		
		curses.start_color ()
		curses.use_default_colors ()
		curses.init_pair (1, curses.COLOR_WHITE, -1)
		curses.init_pair (2, curses.COLOR_BLUE, -1)
		curses.init_pair (3, curses.COLOR_MAGENTA, -1)
		curses.init_pair (4, curses.COLOR_GREEN, -1)
		self._color_text = curses.color_pair (1)
		self._color_markup = curses.color_pair (2)
		self._color_message = curses.color_pair (3)
		self._color_input = curses.color_pair (4)
		
		self._messages = []
		self._messages_touched = False
		self._max_message_lines = 5
		self._max_input_lines = 5
		
		self.show ()
	
	def close (self) :
		
		self.hide ()
		
		del self._window
		del self._window_lines
		del self._window_columns
		del self._color_text
		del self._color_markup
		del self._color_message
		del self._color_input
		del self._messages
		del self._messages_touched
		del self._max_message_lines
		del self._max_input_lines
	
	def show (self) :
		self._window = curses.initscr ()
		curses.raw ()
		curses.noecho ()
		curses.nonl ()
		self._window.keypad (1)
		self._window.leaveok (0)
		(self._window_lines, self._window_columns) = self._window.getmaxyx ()
		self._view.set_max (self._window_lines, self._window_columns - 1)
	
	def hide (self) :
		self._window.keypad (0)
		self._window.leaveok (1)
		curses.nl ()
		curses.echo ()
		curses.noraw ()
		curses.endwin ()
	
	def scan (self) :
		return self._window.getch ()
	
	def flush (self) :
		curses.flushinp ()
	
	def alert (self) :
		curses.beep ()
	
	def notify (self, _format, *_arguments) :
		self._messages.insert (0, _format % _arguments)
		del self._messages[self._max_message_lines :]
		self._messages_touched = True
	
	def loop (self) :
		try :
			self._loop = True
			self.refresh ()
			while self._loop :
				self._handler.handle_key (self, self.scan ())
				self.refresh ()
		except Exception, _error :
			return (_error, traceback.format_exc ())
		except :
			return (None, '<<unknown system error>>')
		return None
	
	def loop_stop (self) :
		self._loop = False
	
	def input (self, _format, *_arguments) :
		
		self._window.move (self._window_lines - self._max_input_lines, 0)
		self._window.clrtobot ()
		self._window.attrset (self._color_input)
		self._window.addstr ('[??] ')
		self._window.addstr (_format % _arguments)
		self._window.move (self._window_lines - self._max_input_lines + 1, 0)
		self._window.addstr ('[>>] ')
		self._window.refresh ()
		
		curses.noraw ()
		curses.echo ()
		try :
			_string = self._window.getstr ()
		except :
			_string = None
		
		curses.raw ()
		curses.noecho ()
		
		return _string
	
	def refresh (self) :
		
		_view = self._view
		_view.correct_marks ()
		
		_scroll = _view.get_scroll ()
		_cursor = _view.get_cursor ()
		_head = _view.get_head ()
		_tail = _view.get_tail ()
		_mark = _view.get_mark ()
		
		_scroll_lines = _scroll.get_length ()
		_cursor_line = _cursor.get_line ()
		_cursor_column = _cursor.get_column ()
		_head_line = _head.get_line ()
		_head_column = _head.get_column ()
		_tail_line = _tail.get_line ()
		_tail_column = _tail.get_column ()
		_mark_line = _mark.get_line ()
		_mark_enabled = _view.is_mark_enabled ()
		_max_lines = self._window_lines
		_max_columns = self._window_columns - 1
		
		_messages = self._messages
		_messages_touched = self._messages_touched
		self._messages_touched = False
		
		_window = self._window
		_color_text = self._color_text
		_color_markup = self._color_markup
		_color_message = self._color_message
		
		_window.erase ()
		
		_color_current = None
		for i in xrange (0, _max_lines) :
			_window.move (i, 0)
			if _color_current != _color_markup :
				_window.attrset (_color_markup)
				_color_current = _color_markup
			_scroll_line = _head_line + i
			if _scroll_line < _scroll_lines :
				if _mark_enabled and (
						(_cursor_line <= _scroll_line <= _mark_line)
						or (_mark_line <= _scroll_line <= _cursor_line)) :
					_window.addstr ('#')
				else :
					_window.addstr (' ')
				_string = _scroll.select (_scroll_line)
				_column = 0
				_code = 0
				for _character in _string :
					_code = ord (_character)
					if _code == 9 :
						_delta = (((_column / 4) + 1) * 4) - _column
						if ((_column + _delta) > _head_column) and (_column <= _tail_column) :
							if _color_current != _color_markup :
								_window.attrset (_color_markup)
								_color_current = _color_markup
							if (_column >= _head_column) and ((_column + _delta) <= _tail_column) :
								_window.addstr ('-' * (_delta - 1))
							else :
								if _column < _head_column :
									_window.addstr ('-' * (_column + _delta - _head_column - 1))
								if _column + _delta > _tail_column :
									_window.addstr ('-' * (_tail_column - _column))
							_window.addstr ('>')
						_column += _delta
					else :
						if _color_current != _color_text :
							_window.attrset (_color_text)
							_color_current = _color_text
						if (_column >= _head_column) and (_column <= _tail_column) :
							_window.addstr (_character.encode ('utf-8'))
						_column += 1
				if _column <= _tail_column and _code == 32 :
					if _color_current != _color_markup :
						_window.attrset (_color_markup)
						_color_current = _color_markup
					_window.addstr ('.')
			else :
				if _color_current != _color_markup :
					_window.attrset (_color_markup)
					_color_current = _color_markup
				_window.addstr ('-----')
				break
		
		_window.move (_cursor_line - _head_line, _cursor_column - _head_column + 1)
		
		if _messages_touched :
			_index = 0
			_window.attrset (_color_message)
			_window.move (_max_lines - len (_messages), 0)
			_window.clrtobot ()
			for _message in _messages :
				_window.move (_max_lines - _index - 1, 0)
				_window.addstr ('[..] ')
				_window.addstr (_message)
				_index += 1
			_window.move (_max_lines - 1, _max_columns - 1)
		
		_window.refresh ()
#


class Handler :
	
	def __init__ (self) :
		pass
	
	def handle_key (self, _shell, _code) :
		
		if _code < 0 :
			self.handle_key_unknown (_shell, 'Code:%d' % (_code))
		
		elif (_code >= 32) and (_code < 127) :
			self.handle_key_character (_shell, chr (_code))
		elif (_code >= 194) and (_code < 224) :
			_char = (chr (_code) + chr (_shell.scan ())) .decode ('utf-8')
			self.handle_key_character (_shell, chr (_code))
		
		elif _code == 8 : # Backspace
			self.handle_key_backspace (_shell)
		elif _code == 9 : # Tab
			self.handle_key_tab (_shell)
		elif _code == 10 : # Enter
			self.handle_key_enter (_shell)
		elif _code == 13 : # Enter
			self.handle_key_enter (_shell)
		elif _code == 27 : # Escape
			self.handle_key_escape (_shell)
		elif _code == 127 : # Delete
			self.handle_key_delete (_shell)
		
		elif (_code >= 0) and (_code < 32) :
			self.handle_key_control (_shell, _code)
		
		elif _code == curses.KEY_UP :
			self.handle_key_up (_shell)
		elif _code == curses.KEY_DOWN :
			self.handle_key_down (_shell)
		elif _code == curses.KEY_LEFT :
			self.handle_key_left (_shell)
		elif _code == curses.KEY_RIGHT :
			self.handle_key_right (_shell)
		
		elif _code == curses.KEY_HOME :
			self.handle_key_home (_shell)
		elif _code == curses.KEY_END :
			self.handle_key_end (_shell)
		
		elif _code == curses.KEY_PPAGE :
			self.handle_key_page_up (_shell)
		elif _code == curses.KEY_NPAGE :
			self.handle_key_page_down (_shell)
		
		elif _code == curses.KEY_IC :
			self.handle_key_insert (_shell)
		elif _code == curses.KEY_DC :
			self.handle_key_delete (_shell)
		
		elif _code == curses.KEY_BACKSPACE :
			self.handle_key_backspace (_shell)
		elif _code == curses.KEY_ENTER :
			self.handle_key_enter (_shell)
		
		elif (_code >= curses.KEY_F0) and (_code <= curses.KEY_F63) :
			self.handle_key_function (_shell, _code - curses.KEY_F0)
		
		else :
			self.handle_key_unknown (_shell, 'Code:%d' % (_code))
		
		return True
	
	def handle_key_backspace (self, _shell) :
		self.handle_key_unknown (_shell, 'Backspace')
	
	def handle_key_tab (self, _shell) :
		self.handle_key_unknown (_shell, 'Tab')
	
	def handle_key_enter (self, _shell) :
		self.handle_key_unknown (_shell, 'Enter')
	
	def handle_key_escape (self, _shell) :
		self.handle_key_unknown (_shell, 'Escape')
	
	def handle_key_delete (self, _shell) :
		self.handle_key_unknown (_shell, 'Delete')
	
	def handle_key_control (self, _shell, _code) :
		self.handle_key_unknown (_shell, 'Ctrl+%s' % (chr (64 + _code)))
	
	def handle_key_character (self, _shell, _character) :
		self.handle_key_unknown (_shell, _character)
	
	def handle_key_up (self, _shell) :
		self.handle_key_unknown (_shell, 'Up')
	
	def handle_key_down (self, _shell) :
		self.handle_key_unknown (_shell, 'Down')
	
	def handle_key_left (self, _shell) :
		self.handle_key_unknown (_shell, 'Left')
	
	def handle_key_right (self, _shell) :
		self.handle_key_unknown (_shell, 'Right')
	
	def handle_key_home (self, _shell) :
		self.handle_key_unknown (_shell, 'Home')
	
	def handle_key_end (self, _shell) :
		self.handle_key_unknown (_shell, 'End')
	
	def handle_key_page_up (self, _shell) :
		self.handle_key_unknown (_shell, 'Page up')
	
	def handle_key_page_down (self, _shell) :
		self.handle_key_unknown (_shell, 'Page down')
	
	def handle_key_insert (self, _shell) :
		self.handle_key_unknown (_shell, 'Insert')
	
	def handle_key_function (self, _shell, _code) :
		self.handle_key_unknown (_shell, 'F%d' % (_code))
	
	def handle_key_unknown (self, _shell, _key) :
		_shell.notify ('Unhandled key [%s]; ignoring.', _key)
#


class ScrollHandler (Handler) :
	
	def __init__ (self) :
		Handler.__init__ (self)
		self._commands = dict ()
		self._controls = dict ()
		self.key_control_code_for_mark = ord ('@') - 64 # or Space
		self.key_control_code_for_command = ord ('R') - 64
		self.key_control_code_for_exit = ord ('X') - 64
		self.key_control_code_for_delete_line = ord ('D') - 64
	
	def handle_key_up (self, _shell) :
		_shell.get_view () .get_cursor () .increment_line (-1)
	
	def handle_key_down (self, _shell) :
		_shell.get_view () .get_cursor () .increment_line (1)
	
	def handle_key_left (self, _shell) :
		_shell.get_view () .get_cursor () .increment_column (-1)
	
	def handle_key_right (self, _shell) :
		_shell.get_view () .get_cursor () .increment_column (1)

	def handle_key_home (self, _shell) :
		_shell.get_view () .get_cursor () .set_column (0)
	
	def handle_key_end (self, _shell) :
		_view = _shell.get_view ()
		_cursor = _view.get_cursor ()
		_cursor.set_column (_view.get_scroll () .select_visual_length (_cursor.get_line ()))
	
	def handle_key_page_up (self, _shell) :
		_shell.get_view () .get_cursor () .increment_line (-32)
	
	def handle_key_page_down (self, _shell) :
		_shell.get_view () .get_cursor () .increment_line (32)
	
	def handle_key_backspace (self, _shell) :
		_view = _shell.get_view ()
		_scroll = _view.get_scroll ()
		_cursor = _view.get_cursor ()
		_line = _cursor.get_line ()
		_visual_column = _cursor.get_column ()
		_length = _scroll.select_visual_length (_line)
		if _visual_column > _length :
			_cursor.set_column (_length)
		elif _visual_column > 0 :
			_real_column = _scroll.select_real_column (_line, _visual_column - 1)
			_scroll.delete (_line, _real_column, 1)
			_cursor.set_column (_scroll.select_visual_column (_line, _real_column))
		elif _line > 0 :
			_length = _scroll.select_visual_length (_line - 1)
			_scroll.unsplit (_line - 1)
			_cursor.increment_line (-1)
			_cursor.set_column (_length)
		else :
			_shell.alert ()
	
	def handle_key_tab (self, _shell) :
		self._insert_character (_shell, '\t')
	
	def handle_key_enter (self, _shell) :
		_view = _shell.get_view ()
		_scroll = _view.get_scroll ()
		_cursor = _view.get_cursor ()
		_line = _cursor.get_line ()
		_scroll.split (_line, _scroll.select_real_column (_line, _cursor.get_column ()))
		_cursor.increment_line (1)
		_cursor.set_column (0)
	
	def handle_key_delete (self, _shell) :
		_view = _shell.get_view ()
		_scroll = _view.get_scroll ()
		_cursor = _view.get_cursor ()
		_line = _cursor.get_line ()
		_visual_column = _cursor.get_column ()
		_length = _scroll.select_visual_length (_line)
		if _visual_column > _length :
			_cursor.set_column (_length)
		elif _visual_column < _length :
			_real_column = _scroll.select_real_column (_line, _visual_column)
			_scroll.delete (_line, _real_column, 1)
			_cursor.set_column (_scroll.select_visual_column (_line, _real_column))
		elif _line < (_scroll.get_length () - 1) :
			_scroll.unsplit (_line)
			_cursor.set_column (_length)
		else :
			_shell.alert ()
	
	def handle_key_character (self, _shell, _character) :
		self._insert_character (_shell, _character)
	
	def _insert_character (self, _shell, _character) :
		_view = _shell.get_view ()
		_scroll = _view.get_scroll ()
		_cursor = _view.get_cursor ()
		_line = _cursor.get_line ()
		_visual_column = _cursor.get_column ()
		_real_column = _scroll.select_real_column (_line, _visual_column)
		_scroll.insert (_line, _real_column, _character)
		_cursor.set_column (_scroll.select_visual_column (_line, _real_column + 1))
	
	def handle_key_control (self, _shell, _code) :
		if _code not in self._controls :
			self.handle_key_unknown (_shell, 'Ctrl+%s' % (chr (64 + _code)))
			return
		_handler = self._controls[_code]
		try :
			_handler (_shell, [])
		except Exception, _error :
			_shell.notify ('Unhandled exception [%s]; ignoring.', str (_error))
		except :
			_shell.notify ('Unhandled system exception; ignoring.')
	
	def handle_command (self, _shell, _arguments) :
		_command = _shell.input ('Command?')
		if _command is None :
			return
		_parts = _command.split ()
		if len (_parts) == 0 :
			return
		if _parts[0] not in self._commands :
			_shell.notify ('Unhandled command [%s]; ignoring.', _parts[0])
			return
		_handler = self._commands[_parts[0]]
		try :
			_handler (_shell, _parts[1 :])
		except Exception, _error :
			_shell.notify ('Unhandled exception [%s]; ignoring.', str (_error))
		except :
			_shell.notify ('Unhandled system exception; ignoring.')
	
	def register_command (self, _command, _handler) :
		self._commands[_command] = _handler
	
	def unregister_command (self, _command) :
		del self._commands[_command]
	
	def register_control (self, _control, _handler) :
		self._controls[ord (_control) - 64] = _handler
	
	def unregister_control (self, _control) :
		del self._controls[ord (_control) - 64]
#


def exit_command (_shell, _arguments) :
	if len (_arguments) != 0 :
		_shell.notify ('exit: wrong syntax: exit')
		return
	_shell.loop_stop ()


def mark_command (_shell, _arguments) :
	if len (_arguments) != 0 :
		_shell.notify ('mark: wrong syntax: mark')
		return
	_view = _shell.get_view ()
	if _view.is_mark_enabled () :
		_view.set_mark_enabled (False)
	else :
		_cursor = _view.get_cursor ()
		_mark = _view.get_mark ()
		_view.set_mark_enabled (True)
		_mark.set_line (_cursor.get_line ())
		_mark.set_column (_cursor.get_column ())


def clear_command (_shell, _arguments) :
	if len (_arguments) != 0 :
		_shell.notify ('clear: wrong syntax: clear')
		return
	_shell.get_view () .get_scroll () .empty ()


_yank_buffer = None


def yank_lines_command (_shell, _arguments) :
	if len (_arguments) != 0 :
		_shell.notify ('yank-lines: wrong syntex: yank-lines')
		return
	if _yank_buffer is None :
		_shell.notify ('yank-lines: yank buffer is empty.')
	_view = _shell.get_view ()
	_scroll = _view.get_scroll ()
	_cursor = _view.get_cursor ()
	_cursor_line = _cursor.get_line ()
	if isinstance(_yank_buffer, list) :
		for _line in _yank_buffer :
			_scroll.include_before (_cursor_line, _line)
	else :
		_visual_column = _cursor.get_column ()
		_real_column = _scroll.select_real_column (_cursor_line, _visual_column)
		_scroll.insert (_cursor_line, _real_column, _yank_buffer)
		_cursor.set_column (_scroll.select_visual_column (_cursor_line, _real_column + len (_yank_buffer)))


def copy_lines_command (_shell, _arguments) :
	global _yank_buffer
	if len (_arguments) != 0 :
		_shell.notify ('copy-lines: wrong syntax: copy-lines')
		return
	_yank_buffer = []
	_view = _shell.get_view ()
	_scroll = _view.get_scroll ()
	_cursor = _view.get_cursor ()
	_cursor_line = _cursor.get_line ()
	if _view.is_mark_enabled () :
		_mark = _view.get_mark ()
		_mark_line = _mark.get_line ()
		if _mark_line == _cursor_line :
			_cursor_real_column = _scroll.select_real_column (_cursor_line, _cursor.get_column ())
			_mark_real_column = _scroll.select_real_column (_cursor_line, _mark.get_column ())
			_first_real_column = min (_mark_real_column, _cursor_real_column)
			_last_real_column = max (_mark_real_column, _cursor_real_column)
			_string = _scroll.select (_cursor_line)
			_yank_buffer = _string[_first_real_column : _last_real_column]
		else :
			_first_line = min (_mark_line, _cursor_line)
			_last_line = max (_mark_line, _cursor_line)
			for _line in xrange (_first_line, _last_line + 1) :
				_yank_buffer.append (_scroll.select (_line))
			_yank_buffer.reverse ()
		_view.set_mark_enabled (False)
	else :
		_yank_buffer.append (_scroll.select (_cursor_line))


def delete_lines_command (_shell, _arguments) :
	global _yank_buffer
	if len (_arguments) != 0 :
		_shell.notify ('delete-lines: wrong syntax: delete-lines')
		return
	_yank_buffer = []
	_view = _shell.get_view ()
	_scroll = _view.get_scroll ()
	_cursor = _view.get_cursor ()
	_cursor_line = _cursor.get_line ()
	if _view.is_mark_enabled () :
		_mark_line = _view.get_mark () .get_line ()
		_first_line = min (_mark_line, _cursor_line)
		_last_line = max (_mark_line, _cursor_line)
		for _line in xrange (_first_line, _last_line + 1) :
			_yank_buffer.append (_scroll.select (_first_line))
			_scroll.exclude (_first_line)
		_view.set_mark_enabled (False)
		_cursor.set_line (_first_line)
	else :
		_yank_buffer.append (_scroll.select (_cursor_line))
		_scroll.exclude (_cursor_line)
	_yank_buffer.reverse ()


def load_command (_shell, _arguments) :
	if len (_arguments) != 2 :
		_shell.notify ('load: wrong syntax: load r|i|a <path>')
		return
	_type = _arguments[0]
	_path = _arguments[1]
	if _type not in ['r', 'i', 'a'] :
		_shell.notify ('load: wrong type; aborting.')
		return
	if not os.path.isfile (_path) :
		_shell.notify ('load: wrong path; aborting.')
		return
	_stream = codecs.open (_path, 'r', 'utf-8')
	_lines = _stream.readlines ()
	_stream.close ()
	_handle_file_lines (_shell, _type, _lines)


def sys_command (_shell, _arguments) :
	if len (_arguments) < 2 :
		_shell.notify ('sys: wrong syntax: sys r|i|a <command> <argument> ...')
		return
	_type = _arguments[0]
	if _type not in ['r', 'i', 'a'] :
		_shell.notify ('sys: wrong type; aborting.')
		return
	_system_arguments = _arguments[1 :]
	_shell.hide ()
	try :
		_process = subprocess.Popen (
				_system_arguments, shell = False, env = None,
				stdin = None, stdout = subprocess.PIPE, stderr = subprocess.PIPE, bufsize = 1, close_fds = True, universal_newlines = True)
	except :
		_shell.show ()
		_shell.notify ('sys: wrong command; aborting.')
		return
	try :
		_stream = codecs.EncodedFile (_process.stdout, 'utf-8')
		_lines = _stream.readlines ()
		_stream.close ()
		_stream = codecs.EncodedFile (_process.stderr, 'utf-8')
		_error_lines = _stream.readlines ()
		_stream.close ()
		_error = _process.wait ()
	except :
		_shell.show ()
		_shell.notify ('sys: command failed; aborting.')
		return
	_shell.show ()
	if _error != 0 :
		_shell.notify ('sys: command failed; ignoring.')
	if len (_error_lines) != 0 :
		for _line in _error_lines :
			_line = _line.rstrip ('\r\n')
			_shell.notify ('sys: %s', _line)
	_handle_file_lines (_shell, _type, _lines)


def _handle_file_lines (_shell, _type, _lines) :
	_view = _shell.get_view ()
	_scroll = _view.get_scroll ()
	if _type == 'r' :
		_scroll.empty ()
		_insert_line = 0
	elif _type == 'i' :
		_insert_line = _view.get_cursor () .get_line ()
	elif _type == 'a' :
		_insert_line = _scroll.get_length () - 1
	else :
		_insert_line = _scroll.get_length () - 1
	_lines.reverse ()
	for _line in _lines :
		_line = _line.rstrip ('\r\n')
		_scroll.include_before (_insert_line, _line)


def sce (_arguments) :
	_scroll = Scroll ()
	_view = View (_scroll)
	_handler = ScrollHandler ()
	#_handler.register_control ('X', exit_command)
	_handler.register_control ('@', mark_command)
	_handler.register_control ('R', _handler.handle_command)
	_handler.register_control ('Y', yank_lines_command)
	_handler.register_control ('D', copy_lines_command)
	_handler.register_control ('K', delete_lines_command)
	_handler.register_command ('clear', clear_command)
	_handler.register_command ('exit', exit_command)
	_handler.register_command ('load', load_command)
	_handler.register_command ('sys', sys_command)
	_shell = Shell (_view, _handler)
	_shell.open ()
	for _argument in sys.argv[1 :] :
		load_command (_shell, ['a', _argument])
	_error = _shell.loop ()
	_shell.close ()
	if _error is not None :
		print _error[0]
		print _error[1]
	print


sce (sys.argv[1 :])
