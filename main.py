import sys
from PyQt4 import QtGui as qt

import processing
import gui


def main():
    app = qt.QApplication(sys.argv)
    main_window = gui.MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
