# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UserLoginWnd.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_UserLoginWnd(object):
    def setupUi(self, UserLoginWnd):
        UserLoginWnd.setObjectName("UserLoginWnd")
        UserLoginWnd.resize(961, 794)
        self.listToPlay = QtWidgets.QListWidget(UserLoginWnd)
        self.listToPlay.setGeometry(QtCore.QRect(40, 170, 431, 601))
        font = QtGui.QFont()
        font.setFamily("宋体")
        font.setPointSize(14)
        self.listToPlay.setFont(font)
        self.listToPlay.setObjectName("listToPlay")
        self.label = QtWidgets.QLabel(UserLoginWnd)
        self.label.setGeometry(QtCore.QRect(140, 20, 221, 41))
        font = QtGui.QFont()
        font.setFamily("隶书")
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.textEdit = QtWidgets.QTextEdit(UserLoginWnd)
        self.textEdit.setGeometry(QtCore.QRect(360, 20, 221, 41))
        self.textEdit.setObjectName("textEdit")
        self.listHistory = QtWidgets.QListView(UserLoginWnd)
        self.listHistory.setGeometry(QtCore.QRect(510, 170, 411, 601))
        font = QtGui.QFont()
        font.setFamily("宋体")
        font.setPointSize(14)
        self.listHistory.setFont(font)
        self.listHistory.setObjectName("listHistory")
        self.label_2 = QtWidgets.QLabel(UserLoginWnd)
        self.label_2.setGeometry(QtCore.QRect(670, 130, 121, 51))
        font = QtGui.QFont()
        font.setFamily("隶书")
        font.setPointSize(16)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(UserLoginWnd)
        self.label_3.setGeometry(QtCore.QRect(180, 130, 151, 51))
        font = QtGui.QFont()
        font.setFamily("隶书")
        font.setPointSize(16)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.Query = QtWidgets.QPushButton(UserLoginWnd)
        self.Query.setGeometry(QtCore.QRect(630, 20, 141, 41))
        font = QtGui.QFont()
        font.setFamily("隶书")
        font.setPointSize(20)
        self.Query.setFont(font)
        self.Query.setObjectName("Query")
        self.Share = QtWidgets.QPushButton(UserLoginWnd)
        self.Share.setGeometry(QtCore.QRect(760, 90, 141, 41))
        font = QtGui.QFont()
        font.setFamily("隶书")
        font.setPointSize(20)
        self.Share.setFont(font)
        self.Share.setObjectName("Share")
        self.Comment = QtWidgets.QPushButton(UserLoginWnd)
        self.Comment.setGeometry(QtCore.QRect(410, 90, 141, 41))
        font = QtGui.QFont()
        font.setFamily("隶书")
        font.setPointSize(20)
        self.Comment.setFont(font)
        self.Comment.setObjectName("Comment")
        self.Praise = QtWidgets.QPushButton(UserLoginWnd)
        self.Praise.setGeometry(QtCore.QRect(50, 90, 141, 41))
        font = QtGui.QFont()
        font.setFamily("隶书")
        font.setPointSize(20)
        self.Praise.setFont(font)
        self.Praise.setObjectName("Praise")

        self.retranslateUi(UserLoginWnd)
        self.Query.clicked.connect(UserLoginWnd.close) # type: ignore
        self.Praise.clicked.connect(UserLoginWnd.close) # type: ignore
        self.Comment.clicked.connect(UserLoginWnd.close) # type: ignore
        self.Share.clicked.connect(UserLoginWnd.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(UserLoginWnd)

    def retranslateUi(self, UserLoginWnd):
        _translate = QtCore.QCoreApplication.translate
        UserLoginWnd.setWindowTitle(_translate("UserLoginWnd", "用户测试"))
        self.label.setText(_translate("UserLoginWnd", "请输入用户 uid："))
        self.label_2.setText(_translate("UserLoginWnd", "历史记录"))
        self.label_3.setText(_translate("UserLoginWnd", "待播放视频"))
        self.Query.setText(_translate("UserLoginWnd", "查询"))
        self.Share.setText(_translate("UserLoginWnd", "分享"))
        self.Comment.setText(_translate("UserLoginWnd", "评论"))
        self.Praise.setText(_translate("UserLoginWnd", "点赞"))
