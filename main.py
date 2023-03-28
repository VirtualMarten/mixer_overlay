import ctypes
from dataclasses import dataclass
import sys
from typing import List
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QPoint
from steamgames import *
from os import environ
from os import path
from ujson import load as json_load, dump as json_dump
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, AudioSession, IAudioEndpointVolume

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
GetWindowTextW = ctypes.windll.user32.GetWindowTextW
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId

BUTTON_COUNT = 8
MIN_WIDTH = 432
MAIN_MARGIN = 25
CONTROL_MARGIN = 35
CLOSE_ON_DESELECT = True
MONITOR = 1
DEBUG = False
AUTO_FILL = True
AUTO_CLOSE = True
GET_STEAM_GAMES = False # Force steam game collection despite cache
STEAM_GAME_CACHE_TIMEOUT = 7200 # cache timeout in minutes
CONFIG_FILE = 'conf.json'
STEAM_GAME_CACHE_FILE = 'games.cache'
CONTROLS_FILE = 'controls.json'
OVERRIDE_STEAMAPP_EXLUSIONS = False
STEAM_LIBRARY_FOLDERS = [ path.join(environ["ProgramFiles(x86)"], 'Steam') ]
STEAMAPP_EXLUSIONS = []
FG_COLOR = '#111'
BG_COLOR = '#eee'
SHOW_PROCESS_COUNT = True
SPACER_POSITION = 0

@dataclass
class Control:
    name: str
    target_applications: List[str]
    use_app_title: bool = False # Use app name instead of control name
    use_app_name: bool = True # Use app title instead of control name
    only_first: bool = False # Only change the volume of the first target app
    exclude: bool = False # App list is inverted, changes all volumes except listed
    master: bool = False # Master volume
    fg_color: str = '' # Text color
    bg_color: str = '' # Background color
    bg_color2: str = '' # Background gradient color

    def __post_init__(self):
        self.target_applications = [ app.lower() for app in self.target_applications ]

CONTROLS = [
    Control("Game", [ '<steamgame>' ]),
    Control("Discord", [ 'discord' ], use_app_name=False)
]

AUTO_FILL_CONTROL = Control("App", [ '<all>' ], False, True, True)

if not path.exists(CONFIG_FILE):
    print('Creating default config file...')
    with open(CONFIG_FILE, 'w') as file:
        json_dump({
            'monitor': MONITOR,
            'button_count': BUTTON_COUNT,
            'auto_close': AUTO_CLOSE,
            'fg_color': FG_COLOR,
            'bg_color': BG_COLOR,
            'auto_fill': AUTO_FILL,
            'auto_fill_control': AUTO_FILL_CONTROL.__dict__,
            'steam_library_folders': STEAM_LIBRARY_FOLDERS,
            'controls': [
                CONTROLS[0].__dict__,
                CONTROLS[1].__dict__
            ]
        }, file, indent=4)
else:
    with open(CONFIG_FILE, 'r') as file:
        config = json_load(file)
        if 'debug' in config:
            DEBUG = config['debug']
        if 'monitor' in config:
            MONITOR = config['monitor']
        if 'control_count' in config:
            BUTTON_COUNT = config['control_count']
        if 'button_count' in config:
            BUTTON_COUNT = config['button_count']
        if 'auto_close' in config:
            AUTO_CLOSE = config['auto_close']
        if 'steam_library_folders' in config:
            STEAM_LIBRARY_FOLDERS = config['steam_library_folders']
        if 'get_steam_games' in config:
            GET_STEAM_GAMES = config['get_steam_games']
        if 'steam_game_cache_timeout' in config:
            STEAM_GAME_CACHE_TIMEOUT = config['steam_game_cache_timeout']
        if 'steam_game_cache_file' in config:
            STEAM_GAME_CACHE_FILE = config['steam_game_cache_file']
        if 'steamapp_exlusions' in config:
            STEAMAPP_EXLUSIONS = config['steamapp_exlusions']
        if 'override_steamapp_exlusions' in config:
            OVERRIDE_STEAMAPP_EXLUSIONS = config['override_steamapp_exlusions']
        if 'fg_color' in config:
            FG_COLOR = config['fg_color']
        if 'bg_color' in config:
            BG_COLOR = config['bg_color']
        if 'show_process_count' in config:
            SHOW_PROCESS_COUNT = config['show_process_count']
        if 'min_width' in config:
            MIN_WIDTH = config['min_width']
        if 'spacer_position' in config:
            SPACER_POSITION = config['spacer_position']
        if 'close_on_deselect' in config:
            CLOSE_ON_DESELECT = config['close_on_deselect']
        if 'auto_fill' in config:
            AUTO_FILL = config['auto_fill']
        if 'auto_fill_control' in config:
            cd = config['auto_fill_control']
            AUTO_FILL_CONTROL = Control(
                name=cd.get('name') or f'Control {len(CONTROLS) + 1}',
                target_applications=cd.get('target_applications') or [],
                use_app_title=cd.get('use_app_title') or False,
                use_app_name=cd.get('use_app_name') or False,
                only_first=cd.get('only_first') or False,
                exclude=cd.get('exclude') or False,
                master=cd.get('master') or False,
                fg_color=cd.get('fg_color') or FG_COLOR,
                bg_color=cd.get('bg_color') or BG_COLOR,
                bg_color2=cd.get('bg_color2') or ''
            )

        if 'controls' in config:
            CONTROLS = []
            for cd in config['controls']:
                CONTROLS.append(Control(
                    name=cd.get('name') or f'Control {len(CONTROLS) + 1}',
                    target_applications=cd.get('target_applications') or [],
                    use_app_title=cd.get('use_app_title') or False,
                    use_app_name=cd.get('use_app_name') or False,
                    only_first=cd.get('only_first') or False,
                    exclude=cd.get('exclude') or False,
                    master=cd.get('master') or False,
                    fg_color=cd.get('fg_color') or FG_COLOR,
                    bg_color=cd.get('bg_color') or BG_COLOR,
                    bg_color2=cd.get('bg_color2') or ''
                ))
        
        for _ in range(BUTTON_COUNT):
            CONTROLS.append(AUTO_FILL_CONTROL)

steam_games = []

if path.exists(STEAM_GAME_CACHE_FILE) and GET_STEAM_GAMES is False:
    steam_games = read_steamgames_cache(STEAM_GAME_CACHE_FILE, STEAM_GAME_CACHE_TIMEOUT)
    if len(steam_games) is None:
        print('Steam game cache out of date')
        steam_games = find_and_write_steamgames_cache(STEAM_LIBRARY_FOLDERS, STEAM_GAME_CACHE_FILE, STEAMAPP_EXLUSIONS)
else:
    steam_games = find_and_write_steamgames_cache(STEAM_LIBRARY_FOLDERS, STEAM_GAME_CACHE_FILE, STEAMAPP_EXLUSIONS)

def get_window_title(hwnd) -> str:
    l = GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(l + 1)
    GetWindowTextW(hwnd, buf, l + 1)
    return buf.value

def get_window_handle_from_pid(pid):
    _hwnd = None
    def enum_windows_cb(hwnd, _):
        nonlocal _hwnd
        _pid = ctypes.c_int(0)
        GetWindowThreadProcessId(hwnd, ctypes.pointer(_pid))
        if _pid.value == pid and _hwnd is None:
            _hwnd = hwnd
        return True
    EnumWindows(EnumWindowsProc(enum_windows_cb), pid)
    return _hwnd

all_sessions = AudioUtilities.GetAllSessions()

class VolumeControlWidget(QtWidgets.QWidget):
    def __init__(self, i, control: Control, sessions: List[AudioSession]):
        super().__init__()

        self.focused = False
        self.control = control
        if not self.control.fg_color:
            self.control.fg_color = FG_COLOR
        if not self.control.bg_color:
            self.control.bg_color = BG_COLOR
        if self.control.master is False:
            self.sessions = sessions
        else:
            self.sessions = []
        self.label = QtWidgets.QLabel(control.name, self)
        self.label.setFont(QtGui.QFont('Times', 20))
        self.label.setStyleSheet('QLabel { color: %s }' % self.control.fg_color)

        self.vl = 1
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        
        self._bg_color = QColor(255, 255, 255, 0)
        self._x_offset = 10

        self.layout = QtWidgets.QHBoxLayout(self)
        margins = self.layout.contentsMargins()
        self.layout.setContentsMargins(self._x_offset, margins.top(), margins.right(), margins.bottom())
        self.setMinimumWidth(MIN_WIDTH)
        self.layout.addWidget(self.label, alignment=Qt.AlignVCenter)

        self.fade_in = QtCore.QPropertyAnimation(
            self,
            b"bg_color",
            parent=self,
            startValue=QColor(255, 255, 255, 0),
            endValue=QColor(self.control.bg_color),
            duration=100
        )

        self.push_offset = QtCore.QPropertyAnimation(
            self,
            b"x_offset",
            parent=self,
            startValue=self._x_offset,
            endValue=30,
            duration=50
        )

        self.unpush_offset = QtCore.QPropertyAnimation(
            self,
            b"x_offset",
            parent=self,
            startValue=30,
            endValue=self._x_offset,
            duration=70
        )

        self.push_offset.setEasingCurve(QtCore.QEasingCurve(QtCore.QEasingCurve.OutBounce))
        self.unpush_offset.setEasingCurve(QtCore.QEasingCurve(QtCore.QEasingCurve.OutCurve))

        QtCore.QTimer().singleShot(i * 50, self.fade_in.start)

        self.change_volume(0)

    def get_title(self):
        if len(self.sessions) == 1:
            pname = self.sessions[0].Process.name()[:-4].capitalize()
            if self.control.use_app_title and self.control.use_app_name:
                title = get_window_title(get_window_handle_from_pid(self.sessions[0].Process.pid))
                if not title:
                    return pname
                elif pname in title:
                    return title
                else:
                    return pname + ': ' + title
            elif self.control.use_app_title:
                return get_window_title(get_window_handle_from_pid(self.sessions[0].Process.pid))
            elif self.control.use_app_name:
                if self.sessions[0].DisplayName:
                    return self.sessions[0].DisplayName
                else:
                    return pname
        return self.control.name

    def get_text(self):
        if DEBUG is True and self.focused is True:
            return f"{self.control.name} {self.vl} \"{'Master' if self.control.master else self.sessions[0].DisplayName or self.get_title()}\" {'master' if self.control.master else self.sessions[0].Process.name()} ({len(self.sessions)})"
        elif SHOW_PROCESS_COUNT and self.focused is True and len(self.sessions) > 1:
            return f"{self.get_title()} - {int(self.vl * 100)}% ({len(self.sessions)})"
        else:
            return f"{self.get_title()} - {int(self.vl * 100)}%"

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRect(0, 0, max(self.width(), MIN_WIDTH), self.height())
        if self.focused:
            gradient = QtGui.QLinearGradient(0, 0, MAIN_MARGIN + rect.width(), 0)
            gradient.setColorAt(0, QColor('#6cfc05'))
            gradient.setColorAt(min(0.99, max(0, self.vl)), QColor('#f9f9f7'))
            gradient.setColorAt(1, QColor('#6cfc05'))
            painter.setBrush(gradient)
        elif self.control.bg_color2:
            gradient = QtGui.QLinearGradient(0, -rect.height() * 2, MAIN_MARGIN + rect.width(), rect.height() * 4)
            gradient.setColorAt(0.30, self.bg_color)
            clr = QColor(self.control.bg_color2)
            clr.alpha = self.bg_color.alpha
            gradient.setColorAt(0.60, clr)
            # gradient.setColorAt(0.60, self.bg_color)
            # gradient.setColorAt(0.70, clr)
            painter.setBrush(gradient)
        else:
            painter.setBrush(self.bg_color)
        painter.setPen(QColor('transparent'))
        painter.drawRoundedRect(rect, 10, 10, Qt.AbsoluteSize)
        self.label.setText(self.get_text())
        if self.focused:
            painter.setBrush(QColor('black'))
            painter.drawPolygon([ QPoint(-1, 10), QPoint((self.height() - 20) / 2, self.height() / 2), QPoint(-1, self.height() - 10) ], Qt.FillRule.WindingFill)
        painter.end()

    @QtCore.Property(QColor)
    def bg_color(self):
        return self._bg_color

    @bg_color.setter
    def bg_color(self, val):
        self._bg_color = val
        self.update()

    @QtCore.Property(float)
    def x_offset(self):
        return self._x_offset

    @x_offset.setter
    def x_offset(self, val):
        self._x_offset = val
        margins = self.layout.contentsMargins()
        self.layout.setContentsMargins(self._x_offset, margins.top(), margins.right(), margins.bottom())

    def change_volume(self, delta: float):
        if self.control.master is True:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
            self.vl = volume.GetMasterVolumeLevelScalar()
            self.vl = max(0, min(1, self.vl + delta))
            volume.SetMasterVolumeLevelScalar(self.vl, None)
        else:
            for session in self.sessions:
                self.vl = session.SimpleAudioVolume.GetMasterVolume()
                self.vl = max(0, min(1, self.vl + delta))
                session.SimpleAudioVolume.SetMasterVolume(self.vl, None)
                if self.control.only_first:
                    break
        if self.parentWidget() is not None:
            self.parentWidget().update()

    def focus(self):
        self.focused = True
        self.push_offset.start()
        self.label.setStyleSheet('QLabel { color: black }')
        self.update()

    def unfocus(self):
        self.focused = False
        self.unpush_offset.start()
        self.label.setStyleSheet('QLabel { color: %s }' % self.control.fg_color)
        self.update()

class OverlayWidget(QtWidgets.QWidget):
    def __init__(self, controls: List[Control]):
        super().__init__()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(MAIN_MARGIN, MAIN_MARGIN, MAIN_MARGIN, MAIN_MARGIN)
        self.layout.setSpacing(CONTROL_MARGIN)

        self.active_controls = []
        self.focused_control = None

        for i, control in enumerate(controls):
            matched_sessions = []
            if control.master is False:
                for session in all_sessions:
                    if session.Process:
                        passed = False
                        session_name = session.Process.name()[:-4].lower()
                        for app in control.target_applications:
                            if app == '<steamgame>':
                                for game in steam_games:
                                    if session_name.startswith(game):
                                        passed = True
                            elif app == '<all>':
                                passed = True
                            elif app[:2] == 'r`' and re.match(app[2:], session_name, re.IGNORECASE) is not None:
                                passed = True
                            elif app[0] == '~' and app[1:] in session_name:
                                passed = True
                            elif app == session_name:
                                passed = True
                        for ac in self.active_controls:
                            if len(ac.sessions) and ac.sessions[0].Process.name()[:-4].lower() == session_name:
                                passed = False
                                break
                        if passed is True:
                            matched_sessions.append(session)
                if control.only_first and len(matched_sessions) > 1:
                    matched_sessions = [ matched_sessions[0] ]

            if len(matched_sessions) or control.master is True:
                self.active_controls.append(VolumeControlWidget(len(self.layout.children()), control, matched_sessions))
                self.layout.addWidget(self.active_controls[-1])
                if len(self.active_controls) == BUTTON_COUNT:
                    break

        # Fill in the extra space
        #for _ in range(BUTTON_COUNT - len(self.active_controls)):
        #self.layout.addStretch(0)
        if SPACER_POSITION > 0:
            self.layout.insertStretch(min(len(self.layout.children()) - 1, SPACER_POSITION - 1), 0)

        self._gradient_opacity = 0

        fade_in = QtCore.QPropertyAnimation(
            self,
            b"gradient_opacity",
            parent=self,
            startValue=0,
            endValue=1,
            duration=120
        )

        fade_in.start()

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        gradient = QtGui.QLinearGradient(self.rect().topLeft(), self.rect().topRight())
        gradient.setColorAt(0, QColor(0, 0, 0, self.gradient_opacity * 255))
        gradient.setColorAt(1, QColor('transparent'))
        painter.fillRect(self.rect(), gradient)
        painter.end()

    @QtCore.Property(float)
    def gradient_opacity(self):
        return self._gradient_opacity

    @gradient_opacity.setter
    def gradient_opacity(self, val):
        self._gradient_opacity = val
        self.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == Qt.Key_Up:
            if self.focused_control is not None:
                self.focused_control.change_volume(0.01)
        elif event.key() == Qt.Key_Down:
            if self.focused_control is not None:
                self.focused_control.change_volume(-0.01)
        else:
            for i, c in enumerate(self.active_controls):
                if event.text() == str(i + 1):
                    if self.focused_control is not None:
                        self.focused_control.unfocus()
                    if self.focused_control == c:
                        if CLOSE_ON_DESELECT is True:
                            sys.exit()
                        self.focused_control = None
                    else:
                        self.focused_control = c
                        c.focus()
                    break

class Overlay(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__(flags=Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background:transparent;")
        self.setCentralWidget(OverlayWidget(CONTROLS))
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == Qt.Key_Escape:
            sys.exit()
        self.centralWidget().keyPressEvent(event)

    def focusOutEvent(self, event: QtGui.QFocusEvent):
        sys.exit()

def changedFocusSlot(old, now):
    if (now == None and QtWidgets.QApplication.activeWindow() != None):
        QtWidgets.QApplication.activeWindow().setFocus()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    QtCore.QObject.connect(app, QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), changedFocusSlot)

    overlay = Overlay()

    screens = QtGui.QScreen.virtualSiblings(overlay.screen())
    monitor = screens[MONITOR].availableGeometry()

    overlay.move(monitor.left(), monitor.top())
    overlay.resize(monitor.size())
    overlay.show()

    app.exec()