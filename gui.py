
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, filename='LOG.txt', filemode='a')


# ------------------------------------------------------------------------------------------------
#   Technical stuff to avoid problems on windows                                                |
# ------------------------------------------------------------------------------------------------

def _append_run_path():
    if getattr(sys, 'frozen', False):
        pathlist = [sys._MEIPASS]

        # If the application is run as a bundle, the pyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS'.

        # the application exe path
        _main_app_path = os.path.dirname(sys.executable)
        pathlist.append(_main_app_path)

        # append to system path enviroment
        os.environ["PATH"] += os.pathsep + os.pathsep.join(pathlist)

_append_run_path()
# -------------------------------------------------------------------------------------------------

import json

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from settings import Settings


class SettingsWindow(QWidget):
    def __init__(self, settings: Settings = None):
        super(SettingsWindow, self).__init__()
        if settings:
            self.settings = settings
        else:
            self.settings = Settings()

        self.init_widgets()

    def set_value(self, widget, param):
        try:
            value = type(self.settings.get_value(param))(widget.text()
                                                         if type(widget) == QLineEdit
                                                         else widget.toPlainText())
            self.settings.set_val(param, value)
            widget.setStyleSheet('background: white')
        except ValueError:
            widget.setStyleSheet('background: pink')

    def set_list(self, widget, param):
        try:
            value = (widget.text()
                     if type(widget) == QLineEdit
                     else widget.toPlainText()).split('\n')
            self.settings.set_val(param, value)
            widget.setStyleSheet('background: white')
        except:
            widget.setStyleSheet('background: pink')

    def text_changed(self, *args):
        editor_iterator = iter(self.editor_widgets)
        for param, value in self.settings.__dict__.items():
            if type(value) == list:
                self.set_list(editor_iterator.__next__(), param)
            else:
                self.set_value(editor_iterator.__next__(), param)

    def init_widgets(self):
        self.label_font = QFont('Arial', 12)
        self.label_font.setBold(True)
        self.editor_font = QFont('Arial', 12)

        self.grid = QGridLayout()
        self.editor_widgets = []
        for param, value in self.settings.__dict__.items():
            editor_name = param.replace('_', ' ').capitalize()
            label = QLabel(editor_name)
            label.setFont(self.label_font)

            if type(value) == list:
                editor = QTextEdit('\n'.join(self.settings.get_value(param)))
                editor.textChanged.connect(self.text_changed)
            else:
                editor = QLineEdit(str(self.settings.get_value(param)))
                editor.textChanged.connect(self.text_changed)
            editor.setFont(self.editor_font)

            self.grid.addWidget(label, len(self.editor_widgets), 0)
            self.grid.addWidget(editor, len(self.editor_widgets), 1)
            self.editor_widgets.append(editor)

        self.setLayout(self.grid)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.classic_settings = Settings()
        self.bfa_settings = Settings()

        with open('settings.txt', 'r', encoding='utf-8') as file:
            settings = json.loads(file.read())

        if 'classic' in settings:
            self.classic_settings.__dict__ = settings['classic']
        if 'bfa' in settings:
            self.bfa_settings.__dict__ = settings['bfa']

        self.classic_settings_window = SettingsWindow(self.classic_settings)
        self.bfa_settings_window = SettingsWindow(self.bfa_settings)

        self.init_widgets()

    def init_widgets(self):
        open_classic_settings = QAction('Classic', self)
        open_bfa_settings = QAction('BFA', self)

        open_classic_settings.triggered.connect(self.open_classic_settings)
        open_bfa_settings.triggered.connect(self.open_bfa_settings)

        self.menuBar().addAction(open_classic_settings)
        self.menuBar().addAction(open_bfa_settings)
        self.open_classic_settings()
        self.setGeometry(200, 200, 600, 400)
        self.show()

    def open_classic_settings(self):
        self.setWindowTitle('Classic settings')
        self.takeCentralWidget()
        self.setCentralWidget(self.classic_settings_window)

    def open_bfa_settings(self):
        self.setWindowTitle('BFA settings')
        self.takeCentralWidget()
        self.setCentralWidget(self.bfa_settings_window)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())