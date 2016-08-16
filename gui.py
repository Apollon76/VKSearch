import copy
import functools
import socket

from PyQt4 import QtGui as qt, QtCore
import urllib.request
import urllib.error

import processing
import tools


def make_frame(parent):
    frame = qt.QFrame(parent)
    frame.setFrameShape(qt.QFrame.StyledPanel)
    layout = qt.QHBoxLayout(frame)
    frame.setLayout(layout)
    return frame, layout


class IdPanel(qt.QWidget):
    def __init__(self, user_id, signal):
        super(IdPanel, self).__init__()
        import API
        self.user = API.User.get_by_id(user_id)
        self.delete_signal = signal
        self.initUI()

    def initUI(self):
        layout = qt.QHBoxLayout()

        nameLabel = qt.QLabel('{} {}'.format(self.user.name, self.user.surname))

        deleteButton = qt.QPushButton('', self)
        deleteButton.setIcon(qt.QIcon('images/delete.png'))  # TODO
        deleteButton.setIconSize(QtCore.QSize(20,20))
        deleteButton.setFixedSize(20, 20)
        deleteButton.clicked.connect(self.remove)

        layout.addWidget(nameLabel)
        layout.addWidget(deleteButton)

        self.setLayout(layout)

    def remove(self):
        self.emit(self.delete_signal, self)


class IdList(qt.QWidget):
    def __init__(self, signal):
        super(IdList, self).__init__()
        self.id_list = []
        self.update_signal = signal
        self.delete_signal = QtCore.SIGNAL('delete_id(PyQt_PyObject)')
        self.initUI()

    def initUI(self):
        layout = qt.QVBoxLayout()

        user_id = qt.QLabel('ID:')
        self.idEdit = qt.QLineEdit()
        addButton = qt.QPushButton('Добавить', self)
        addButton.clicked.connect(self.add_id)
        inputIdFrame, inputIdLayout = make_frame(self)
        inputIdLayout.addWidget(user_id)
        inputIdLayout.addWidget(self.idEdit)
        inputIdLayout.addWidget(addButton)

        self.addedUsers = tools.scrollable(qt.QWidget)(self)
        self.addedUsers.setLayout(qt.QVBoxLayout())

        searchButton = qt.QPushButton('Искать', self)
        searchButton.clicked.connect(self.merge_lists)

        layout.addWidget(inputIdFrame)
        layout.addWidget(self.addedUsers.scrollArea)
        layout.addWidget(searchButton)

        self.setLayout(layout)
        self.setMinimumWidth(300)

    def add_id(self):
        new_id = self.idEdit.text()
        self.idEdit.setText('')
        try:
            new_widget = IdPanel(new_id, self.delete_signal)
            self.id_list.append(new_widget.user.user_id)
            self.addedUsers.layout().addWidget(new_widget)
            self.connect(new_widget, self.delete_signal, self.delete_id)
        except ValueError:
            return

    def delete_id(self, widget):
        user_id = widget.user.user_id
        self.id_list.remove(user_id)
        widget.deleteLater()

    def merge_lists(self):
        thread = QtCore.QThread(self)
        thread.run = lambda: self.process_event(processing.merge_friends, self.id_list, self.update_signal)
        thread.start()

    def process_event(self, target, args, signal):
        try:
            data = target(args)
            self.emit(signal, data)
        except ValueError:
            return


class UserInfo(qt.QWidget):
    def __init__(self, data):
        super(UserInfo, self).__init__()
        self.big_picture_window = None
        self.user = data[1]
        self.frequency = data[0]
        self.avatar = None
        self.initUI()

    def initUI(self):
        layout = qt.QHBoxLayout()

        image = qt.QPixmap('images/loading.png')  # TODO
        image = image.scaled(QtCore.QSize(50, 50))
        self.avatar = qt.QLabel(self)
        self.avatar.setPixmap(qt.QPixmap(image))
        tools.clickable(self.avatar).connect(self.show_big_photo)

        nameLabel = qt.QLabel('<a href=https://vk.com/id{}>{} {}</a>'.format(self.user.user_id, self.user.name, self.user.surname))
        nameLabel.setOpenExternalLinks(True)

        frequencyLabel = qt.QLabel(str(self.frequency))

        layout.addWidget(self.avatar)
        layout.addWidget(nameLabel)
        layout.addWidget(frequencyLabel)

        self.setLayout(layout)

    def setAvatar(self, image_data):
        image = qt.QImage()
        image.loadFromData(image_data)
        self.avatar.setPixmap(qt.QPixmap(image))

    def show_big_photo(self):
        try:
            image_data = urllib.request.urlopen(self.user.get_original_photo(), timeout=1).read()
        except urllib.error.URLError:
            return
        self.big_picture_window = qt.QWidget()

        layout = qt.QHBoxLayout(self.big_picture_window)

        image = qt.QImage()
        image.loadFromData(image_data)
        picture_label = qt.QLabel(self.big_picture_window)
        picture_label.setPixmap(qt.QPixmap(image))
        picture_label.setFixedSize(QtCore.QSize(400, 400))

        layout.addWidget(picture_label)

        self.big_picture_window.setLayout(layout)
        tools.clickable(self.big_picture_window).connect(self.big_picture_window.close)
        self.big_picture_window.setWindowTitle('Фото')
        self.big_picture_window.show()


class PresentationPanel(qt.QWidget):
    def __init__(self):
        super(PresentationPanel, self).__init__()
        self.userList = None
        self.upload_avatar_calls = []
        self.uploader = tools.Demon()
        self.initUI()

    def initUI(self):
        layout = qt.QVBoxLayout()

        self.userList = tools.scrollable(qt.QWidget)(self)
        self.userList.setLayout(qt.QVBoxLayout())

        layout.addWidget(self.userList.scrollArea)

        self.setLayout(layout)
        self.setMinimumWidth(400)

    def updateList(self, value):
        self.uploader.stop()
        update = lambda widget, image: widget.setAvatar(image)
        for i in reversed(range(self.userList.layout().count())):
            widget = self.userList.layout().itemAt(i).widget()
            self.disconnect(self, QtCore.SIGNAL('upload_avatar{}(PyQt_PyObject)'.format(i)), self.upload_avatar_calls[i])
            widget.deleteLater()
        users = list(map(lambda x: x[1], value))
        users = copy.deepcopy(users)
        self.uploader = tools.Demon(target=self.upload_avatars, args=(users, ))
        self.upload_avatar_calls.clear()
        for num, i in enumerate(value):
            new_widget = UserInfo(i)
            self.userList.layout().addWidget(new_widget)
            self.upload_avatar_calls.append(functools.partial(update, new_widget))
            self.connect(self, QtCore.SIGNAL('upload_avatar{}(PyQt_PyObject)'.format(num)), self.upload_avatar_calls[num])
        self.uploader.start()
        vbar = self.userList.scrollArea.verticalScrollBar()
        vbar.setValue(vbar.minimum())

    def upload_avatars(self, stopped, users: list):
        for i, user in enumerate(users):
            if stopped.get():
                break
            try:
                image_data = urllib.request.urlopen(user.get_photo(), timeout=1).read()
                self.emit(QtCore.SIGNAL('upload_avatar{}(PyQt_PyObject)'.format(i)), image_data)
            except urllib.error.URLError:
                continue
            except socket.timeout:
                continue


class SearchPanel(qt.QWidget):
    def __init__(self):
        super(SearchPanel, self).__init__()
        self.initUI()

    def initUI(self):
        self.idList = IdList(QtCore.SIGNAL('updateList(PyQt_PyObject)'))
        listFrame, listLayout = make_frame(self)
        listLayout.addWidget(self.idList)

        self.userPanel = PresentationPanel()
        userPanelFrame, userPanelLayout = make_frame(self)
        userPanelLayout.addWidget(self.userPanel)

        self.connect(self.idList, QtCore.SIGNAL('updateList(PyQt_PyObject)'), self.userPanel.updateList)

        splitter = qt.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(listFrame)
        splitter.addWidget(userPanelFrame)

        layout = qt.QHBoxLayout()

        layout.addWidget(splitter)

        self.setLayout(layout)


class MainWindow(qt.QMainWindow):
    def __init__(self,):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Totally search')
        search_panel = SearchPanel()
        self.setCentralWidget(search_panel)

        exitAction = qt.QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.setGeometry(300, 300, 600, 350)
