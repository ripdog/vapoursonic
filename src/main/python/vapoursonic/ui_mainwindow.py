# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources\base\mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_vapoursonic(object):
    def setupUi(self, vapoursonic):
        vapoursonic.setObjectName("vapoursonic")
        vapoursonic.resize(1500, 1200)
        self.centralwidget = QtWidgets.QWidget(vapoursonic)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.stackedWidget.setStyleSheet("")
        self.stackedWidget.setObjectName("stackedWidget")
        self.connectionSetup = QtWidgets.QWidget()
        self.connectionSetup.setObjectName("connectionSetup")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.connectionSetup)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(250, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.passwordInput = QtWidgets.QLineEdit(self.connectionSetup)
        self.passwordInput.setObjectName("passwordInput")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.passwordInput)
        self.passwordLabel = QtWidgets.QLabel(self.connectionSetup)
        self.passwordLabel.setObjectName("passwordLabel")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.passwordLabel)
        self.connectButton = QtWidgets.QPushButton(self.connectionSetup)
        self.connectButton.setObjectName("connectButton")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.SpanningRole, self.connectButton)
        self.usernameInput = QtWidgets.QLineEdit(self.connectionSetup)
        self.usernameInput.setObjectName("usernameInput")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.usernameInput)
        self.domainInput = QtWidgets.QLineEdit(self.connectionSetup)
        self.domainInput.setObjectName("domainInput")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.domainInput)
        self.usernameLabel = QtWidgets.QLabel(self.connectionSetup)
        self.usernameLabel.setObjectName("usernameLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.usernameLabel)
        self.domainLabel = QtWidgets.QLabel(self.connectionSetup)
        self.domainLabel.setObjectName("domainLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.domainLabel)
        spacerItem1 = QtWidgets.QSpacerItem(20, 200, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout.setItem(0, QtWidgets.QFormLayout.FieldRole, spacerItem1)
        self.horizontalLayout.addLayout(self.formLayout)
        spacerItem2 = QtWidgets.QSpacerItem(250, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.stackedWidget.addWidget(self.connectionSetup)
        self.mainPage = QtWidgets.QWidget()
        self.mainPage.setObjectName("mainPage")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.mainPage)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.splitter_2 = QtWidgets.QSplitter(self.mainPage)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.splitter_2.setChildrenCollapsible(False)
        self.splitter_2.setObjectName("splitter_2")
        self.splitter = QtWidgets.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.albumTreeListSearch = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.albumTreeListSearch.setContentsMargins(0, 0, 0, 0)
        self.albumTreeListSearch.setObjectName("albumTreeListSearch")
        self.search = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.search.setObjectName("search")
        self.albumTreeListSearch.addWidget(self.search)
        self.backHomeButtonLayout = QtWidgets.QWidget(self.verticalLayoutWidget_3)
        self.backHomeButtonLayout.setEnabled(True)
        self.backHomeButtonLayout.setMinimumSize(QtCore.QSize(0, 50))
        self.backHomeButtonLayout.setMaximumSize(QtCore.QSize(16777215, 35))
        self.backHomeButtonLayout.setObjectName("backHomeButtonLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.backHomeButtonLayout)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.backHomeButton = QtWidgets.QPushButton(self.backHomeButtonLayout)
        self.backHomeButton.setMinimumSize(QtCore.QSize(200, 35))
        self.backHomeButton.setIconSize(QtCore.QSize(36, 36))
        self.backHomeButton.setFlat(True)
        self.backHomeButton.setObjectName("backHomeButton")
        self.horizontalLayout_2.addWidget(self.backHomeButton)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.albumTreeListTitle = QtWidgets.QLabel(self.backHomeButtonLayout)
        self.albumTreeListTitle.setObjectName("albumTreeListTitle")
        self.horizontalLayout_2.addWidget(self.albumTreeListTitle)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.albumListViewPreviousPage = QtWidgets.QPushButton(self.backHomeButtonLayout)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumListViewPreviousPage.sizePolicy().hasHeightForWidth())
        self.albumListViewPreviousPage.setSizePolicy(sizePolicy)
        self.albumListViewPreviousPage.setMinimumSize(QtCore.QSize(35, 35))
        self.albumListViewPreviousPage.setMaximumSize(QtCore.QSize(35, 35))
        self.albumListViewPreviousPage.setFlat(True)
        self.albumListViewPreviousPage.setObjectName("albumListViewPreviousPage")
        self.horizontalLayout_2.addWidget(self.albumListViewPreviousPage)
        self.albumListViewRefresh = QtWidgets.QPushButton(self.backHomeButtonLayout)
        self.albumListViewRefresh.setMinimumSize(QtCore.QSize(35, 35))
        self.albumListViewRefresh.setMaximumSize(QtCore.QSize(35, 35))
        self.albumListViewRefresh.setFlat(True)
        self.albumListViewRefresh.setObjectName("albumListViewRefresh")
        self.horizontalLayout_2.addWidget(self.albumListViewRefresh)
        self.albumListViewNextPage = QtWidgets.QPushButton(self.backHomeButtonLayout)
        self.albumListViewNextPage.setMinimumSize(QtCore.QSize(35, 35))
        self.albumListViewNextPage.setMaximumSize(QtCore.QSize(35, 35))
        self.albumListViewNextPage.setFlat(True)
        self.albumListViewNextPage.setObjectName("albumListViewNextPage")
        self.horizontalLayout_2.addWidget(self.albumListViewNextPage)
        self.albumTreeListSearch.addWidget(self.backHomeButtonLayout)
        self.albumTreeList = QtWidgets.QTreeView(self.verticalLayoutWidget_3)
        self.albumTreeList.setMinimumSize(QtCore.QSize(500, 0))
        self.albumTreeList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.albumTreeList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.albumTreeList.setObjectName("albumTreeList")
        self.albumTreeList.header().setDefaultSectionSize(17)
        self.albumTreeListSearch.addWidget(self.albumTreeList)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.selectAlbumDetailsAndListLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.selectAlbumDetailsAndListLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.selectAlbumDetailsAndListLayout.setContentsMargins(0, 0, 0, 0)
        self.selectAlbumDetailsAndListLayout.setObjectName("selectAlbumDetailsAndListLayout")
        self.selectedAlbumDetails = QtWidgets.QHBoxLayout()
        self.selectedAlbumDetails.setObjectName("selectedAlbumDetails")
        self.selectedAlbumArt = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectedAlbumArt.sizePolicy().hasHeightForWidth())
        self.selectedAlbumArt.setSizePolicy(sizePolicy)
        self.selectedAlbumArt.setMinimumSize(QtCore.QSize(128, 128))
        self.selectedAlbumArt.setMaximumSize(QtCore.QSize(128, 128))
        self.selectedAlbumArt.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.selectedAlbumArt.setObjectName("selectedAlbumArt")
        self.selectedAlbumDetails.addWidget(self.selectedAlbumArt)
        self.selectedAlbumTextDetails = QtWidgets.QVBoxLayout()
        self.selectedAlbumTextDetails.setObjectName("selectedAlbumTextDetails")
        self.selectedAlbumTitle = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.selectedAlbumTitle.setMinimumSize(QtCore.QSize(0, 64))
        self.selectedAlbumTitle.setMaximumSize(QtCore.QSize(600, 128))
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.selectedAlbumTitle.setFont(font)
        self.selectedAlbumTitle.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.selectedAlbumTitle.setObjectName("selectedAlbumTitle")
        self.selectedAlbumTextDetails.addWidget(self.selectedAlbumTitle)
        self.selectedAlbumArtist = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.selectedAlbumArtist.setMaximumSize(QtCore.QSize(600, 48))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.selectedAlbumArtist.setFont(font)
        self.selectedAlbumArtist.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.selectedAlbumArtist.setObjectName("selectedAlbumArtist")
        self.selectedAlbumTextDetails.addWidget(self.selectedAlbumArtist)
        self.selectedAlbumTextDetailsMinor = QtWidgets.QHBoxLayout()
        self.selectedAlbumTextDetailsMinor.setObjectName("selectedAlbumTextDetailsMinor")
        self.selectedAlbumTrackCountIcon = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectedAlbumTrackCountIcon.sizePolicy().hasHeightForWidth())
        self.selectedAlbumTrackCountIcon.setSizePolicy(sizePolicy)
        self.selectedAlbumTrackCountIcon.setMinimumSize(QtCore.QSize(24, 0))
        self.selectedAlbumTrackCountIcon.setMaximumSize(QtCore.QSize(24, 24))
        self.selectedAlbumTrackCountIcon.setObjectName("selectedAlbumTrackCountIcon")
        self.selectedAlbumTextDetailsMinor.addWidget(self.selectedAlbumTrackCountIcon)
        self.selectedAlbumTrackCount = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectedAlbumTrackCount.sizePolicy().hasHeightForWidth())
        self.selectedAlbumTrackCount.setSizePolicy(sizePolicy)
        self.selectedAlbumTrackCount.setMaximumSize(QtCore.QSize(16777215, 24))
        self.selectedAlbumTrackCount.setObjectName("selectedAlbumTrackCount")
        self.selectedAlbumTextDetailsMinor.addWidget(self.selectedAlbumTrackCount)
        self.selectedAlbumTotalLengthIcon = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.selectedAlbumTotalLengthIcon.setMaximumSize(QtCore.QSize(24, 24))
        self.selectedAlbumTotalLengthIcon.setObjectName("selectedAlbumTotalLengthIcon")
        self.selectedAlbumTextDetailsMinor.addWidget(self.selectedAlbumTotalLengthIcon)
        self.selectedAlbumTotalLength = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.selectedAlbumTotalLength.setMaximumSize(QtCore.QSize(16777215, 24))
        self.selectedAlbumTotalLength.setObjectName("selectedAlbumTotalLength")
        self.selectedAlbumTextDetailsMinor.addWidget(self.selectedAlbumTotalLength)
        self.selectedAlbumReleaseYearIcon = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.selectedAlbumReleaseYearIcon.setMaximumSize(QtCore.QSize(24, 24))
        self.selectedAlbumReleaseYearIcon.setObjectName("selectedAlbumReleaseYearIcon")
        self.selectedAlbumTextDetailsMinor.addWidget(self.selectedAlbumReleaseYearIcon)
        self.selectedAlbumReleaseYear = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.selectedAlbumReleaseYear.setMaximumSize(QtCore.QSize(16777215, 24))
        self.selectedAlbumReleaseYear.setObjectName("selectedAlbumReleaseYear")
        self.selectedAlbumTextDetailsMinor.addWidget(self.selectedAlbumReleaseYear)
        self.selectedAlbumTextDetails.addLayout(self.selectedAlbumTextDetailsMinor)
        self.selectedAlbumDetails.addLayout(self.selectedAlbumTextDetails)
        self.selectAlbumDetailsAndListLayout.addLayout(self.selectedAlbumDetails)
        self.albumTrackList = QtWidgets.QTreeView(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumTrackList.sizePolicy().hasHeightForWidth())
        self.albumTrackList.setSizePolicy(sizePolicy)
        self.albumTrackList.setMinimumSize(QtCore.QSize(500, 0))
        self.albumTrackList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.albumTrackList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.albumTrackList.setObjectName("albumTrackList")
        self.selectAlbumDetailsAndListLayout.addWidget(self.albumTrackList)
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.splitter_2)
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.playQueueListLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.playQueueListLayout.setContentsMargins(0, 0, 0, 0)
        self.playQueueListLayout.setObjectName("playQueueListLayout")
        self.playQueueList = PlayQueueView(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.playQueueList.sizePolicy().hasHeightForWidth())
        self.playQueueList.setSizePolicy(sizePolicy)
        self.playQueueList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.playQueueList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.playQueueList.setObjectName("playQueueList")
        self.playQueueListLayout.addWidget(self.playQueueList)
        self.playQueueToolboxLayout = QtWidgets.QVBoxLayout()
        self.playQueueToolboxLayout.setObjectName("playQueueToolboxLayout")
        self.toggleFollowPlayedTrackButton = QtWidgets.QToolButton(self.horizontalLayoutWidget)
        self.toggleFollowPlayedTrackButton.setCheckable(True)
        self.toggleFollowPlayedTrackButton.setObjectName("toggleFollowPlayedTrackButton")
        self.playQueueToolboxLayout.addWidget(self.toggleFollowPlayedTrackButton)
        self.repeatPlayQueueButton = QtWidgets.QToolButton(self.horizontalLayoutWidget)
        self.repeatPlayQueueButton.setCheckable(True)
        self.repeatPlayQueueButton.setObjectName("repeatPlayQueueButton")
        self.playQueueToolboxLayout.addWidget(self.repeatPlayQueueButton)
        self.shufflePlayqueueButton = QtWidgets.QToolButton(self.horizontalLayoutWidget)
        self.shufflePlayqueueButton.setObjectName("shufflePlayqueueButton")
        self.playQueueToolboxLayout.addWidget(self.shufflePlayqueueButton)
        self.volumeSliderLabel = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.volumeSliderLabel.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.volumeSliderLabel.setObjectName("volumeSliderLabel")
        self.playQueueToolboxLayout.addWidget(self.volumeSliderLabel)
        self.volumeSlider = QtWidgets.QSlider(self.horizontalLayoutWidget)
        self.volumeSlider.setOrientation(QtCore.Qt.Vertical)
        self.volumeSlider.setObjectName("volumeSlider")
        self.playQueueToolboxLayout.addWidget(self.volumeSlider)
        self.playQueueListLayout.addLayout(self.playQueueToolboxLayout)
        self.gridLayout_3.addWidget(self.splitter_2, 0, 0, 1, 1)
        self.nowPlayingLayout = QtWidgets.QHBoxLayout()
        self.nowPlayingLayout.setSpacing(0)
        self.nowPlayingLayout.setObjectName("nowPlayingLayout")
        self.playingAlbumArt = QtWidgets.QLabel(self.mainPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.playingAlbumArt.sizePolicy().hasHeightForWidth())
        self.playingAlbumArt.setSizePolicy(sizePolicy)
        self.playingAlbumArt.setMinimumSize(QtCore.QSize(60, 60))
        self.playingAlbumArt.setMaximumSize(QtCore.QSize(60, 60))
        self.playingAlbumArt.setObjectName("playingAlbumArt")
        self.nowPlayingLayout.addWidget(self.playingAlbumArt)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.currentPlayingLabel = QtWidgets.QLabel(self.mainPage)
        self.currentPlayingLabel.setMaximumSize(QtCore.QSize(300, 16777215))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.currentPlayingLabel.setFont(font)
        self.currentPlayingLabel.setObjectName("currentPlayingLabel")
        self.verticalLayout.addWidget(self.currentPlayingLabel)
        self.trackArtistName = QtWidgets.QLabel(self.mainPage)
        self.trackArtistName.setMaximumSize(QtCore.QSize(300, 16777215))
        self.trackArtistName.setObjectName("trackArtistName")
        self.verticalLayout.addWidget(self.trackArtistName)
        self.nowPlayingLayout.addLayout(self.verticalLayout)
        self.trackProgressBar = QtWidgets.QSlider(self.mainPage)
        self.trackProgressBar.setTracking(False)
        self.trackProgressBar.setOrientation(QtCore.Qt.Horizontal)
        self.trackProgressBar.setObjectName("trackProgressBar")
        self.nowPlayingLayout.addWidget(self.trackProgressBar)
        self.trackProgressIndicator = QtWidgets.QLabel(self.mainPage)
        self.trackProgressIndicator.setObjectName("trackProgressIndicator")
        self.nowPlayingLayout.addWidget(self.trackProgressIndicator)
        self.prevTrack = QtWidgets.QToolButton(self.mainPage)
        self.prevTrack.setMinimumSize(QtCore.QSize(30, 30))
        self.prevTrack.setStyleSheet("margin:0;\n"
"                                                        padding:0;\n"
"                                                    ")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("."), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.prevTrack.setIcon(icon)
        self.prevTrack.setObjectName("prevTrack")
        self.nowPlayingLayout.addWidget(self.prevTrack)
        self.playPause = QtWidgets.QToolButton(self.mainPage)
        self.playPause.setMinimumSize(QtCore.QSize(30, 30))
        self.playPause.setAutoFillBackground(False)
        self.playPause.setStyleSheet("margin:0;padding:0")
        self.playPause.setIcon(icon)
        self.playPause.setArrowType(QtCore.Qt.NoArrow)
        self.playPause.setObjectName("playPause")
        self.nowPlayingLayout.addWidget(self.playPause)
        self.nextTrack = QtWidgets.QToolButton(self.mainPage)
        self.nextTrack.setMinimumSize(QtCore.QSize(30, 30))
        self.nextTrack.setStyleSheet("margin:0;\n"
"                                                        padding:0;\n"
"                                                    ")
        self.nextTrack.setIcon(icon)
        self.nextTrack.setObjectName("nextTrack")
        self.nowPlayingLayout.addWidget(self.nextTrack)
        self.stop = QtWidgets.QToolButton(self.mainPage)
        self.stop.setMinimumSize(QtCore.QSize(30, 30))
        self.stop.setStyleSheet("margin:0;\n"
"                                                        padding:0;\n"
"                                                    ")
        self.stop.setIcon(icon)
        self.stop.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.stop.setArrowType(QtCore.Qt.NoArrow)
        self.stop.setObjectName("stop")
        self.nowPlayingLayout.addWidget(self.stop)
        self.gridLayout_3.addLayout(self.nowPlayingLayout, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.mainPage)
        self.gridLayout.addWidget(self.stackedWidget, 0, 0, 1, 1)
        vapoursonic.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(vapoursonic)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1500, 17))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        vapoursonic.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(vapoursonic)
        self.statusbar.setObjectName("statusbar")
        vapoursonic.setStatusBar(self.statusbar)
        self.actionConnect = QtWidgets.QAction(vapoursonic)
        self.actionConnect.setObjectName("actionConnect")
        self.actionExit = QtWidgets.QAction(vapoursonic)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionConnect)
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(vapoursonic)
        self.stackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(vapoursonic)
        vapoursonic.setTabOrder(self.domainInput, self.usernameInput)
        vapoursonic.setTabOrder(self.usernameInput, self.passwordInput)
        vapoursonic.setTabOrder(self.passwordInput, self.connectButton)
        vapoursonic.setTabOrder(self.connectButton, self.search)
        vapoursonic.setTabOrder(self.search, self.backHomeButton)
        vapoursonic.setTabOrder(self.backHomeButton, self.albumListViewPreviousPage)
        vapoursonic.setTabOrder(self.albumListViewPreviousPage, self.albumListViewRefresh)
        vapoursonic.setTabOrder(self.albumListViewRefresh, self.albumListViewNextPage)
        vapoursonic.setTabOrder(self.albumListViewNextPage, self.albumTreeList)
        vapoursonic.setTabOrder(self.albumTreeList, self.albumTrackList)
        vapoursonic.setTabOrder(self.albumTrackList, self.playQueueList)
        vapoursonic.setTabOrder(self.playQueueList, self.toggleFollowPlayedTrackButton)
        vapoursonic.setTabOrder(self.toggleFollowPlayedTrackButton, self.repeatPlayQueueButton)
        vapoursonic.setTabOrder(self.repeatPlayQueueButton, self.shufflePlayqueueButton)
        vapoursonic.setTabOrder(self.shufflePlayqueueButton, self.volumeSlider)
        vapoursonic.setTabOrder(self.volumeSlider, self.trackProgressBar)
        vapoursonic.setTabOrder(self.trackProgressBar, self.prevTrack)
        vapoursonic.setTabOrder(self.prevTrack, self.playPause)
        vapoursonic.setTabOrder(self.playPause, self.nextTrack)
        vapoursonic.setTabOrder(self.nextTrack, self.stop)

    def retranslateUi(self, vapoursonic):
        _translate = QtCore.QCoreApplication.translate
        vapoursonic.setWindowTitle(_translate("vapoursonic", "vapoursonic"))
        self.passwordLabel.setText(_translate("vapoursonic", "Password"))
        self.connectButton.setText(_translate("vapoursonic", "Connect"))
        self.usernameLabel.setText(_translate("vapoursonic", "Username"))
        self.domainLabel.setText(_translate("vapoursonic", "Domain"))
        self.backHomeButton.setToolTip(_translate("vapoursonic", "Return to the home screen."))
        self.backHomeButton.setText(_translate("vapoursonic", "Back"))
        self.albumTreeListTitle.setText(_translate("vapoursonic", "Home"))
        self.albumListViewPreviousPage.setToolTip(_translate("vapoursonic", "Return to the previous page of query\n"
"                                                                                results.\n"
"                                                                            "))
        self.albumListViewPreviousPage.setText(_translate("vapoursonic", "Prev"))
        self.albumListViewRefresh.setToolTip(_translate("vapoursonic", "Refresh the current view."))
        self.albumListViewRefresh.setText(_translate("vapoursonic", "Refresh"))
        self.albumListViewNextPage.setToolTip(_translate("vapoursonic", "Advance to the next page of query\n"
"                                                                                results.\n"
"                                                                            "))
        self.albumListViewNextPage.setText(_translate("vapoursonic", "Next"))
        self.selectedAlbumArt.setText(_translate("vapoursonic", "Album Art"))
        self.selectedAlbumTitle.setText(_translate("vapoursonic", "Title"))
        self.selectedAlbumArtist.setText(_translate("vapoursonic", "Artist"))
        self.selectedAlbumTrackCountIcon.setToolTip(_translate("vapoursonic", "The total number of\n"
"                                                                                            songs in this album.\n"
"                                                                                        "))
        self.selectedAlbumTrackCountIcon.setText(_translate("vapoursonic", "CounIcon"))
        self.selectedAlbumTrackCount.setToolTip(_translate("vapoursonic", "The total number of\n"
"                                                                                            songs in this album.\n"
"                                                                                        "))
        self.selectedAlbumTrackCount.setText(_translate("vapoursonic", "Count"))
        self.selectedAlbumTotalLengthIcon.setToolTip(_translate("vapoursonic", "The total length of this\n"
"                                                                                            album.\n"
"                                                                                        "))
        self.selectedAlbumTotalLengthIcon.setText(_translate("vapoursonic", "LengthIcon"))
        self.selectedAlbumTotalLength.setToolTip(_translate("vapoursonic", "The total length of this\n"
"                                                                                            album.\n"
"                                                                                        "))
        self.selectedAlbumTotalLength.setText(_translate("vapoursonic", "Length"))
        self.selectedAlbumReleaseYearIcon.setToolTip(_translate("vapoursonic", "The year this album was\n"
"                                                                                            released.\n"
"                                                                                        "))
        self.selectedAlbumReleaseYearIcon.setText(_translate("vapoursonic", "YearIcon"))
        self.selectedAlbumReleaseYear.setToolTip(_translate("vapoursonic", "The year this album was\n"
"                                                                                            released.\n"
"                                                                                        "))
        self.selectedAlbumReleaseYear.setText(_translate("vapoursonic", "Year"))
        self.toggleFollowPlayedTrackButton.setToolTip(_translate("vapoursonic", "Toggle whether the play queue selects the\n"
"                                                                        currently playing song.\n"
"                                                                    "))
        self.toggleFollowPlayedTrackButton.setText(_translate("vapoursonic", "..."))
        self.repeatPlayQueueButton.setText(_translate("vapoursonic", "..."))
        self.shufflePlayqueueButton.setToolTip(_translate("vapoursonic", "Shuffles the play queue."))
        self.shufflePlayqueueButton.setText(_translate("vapoursonic", "..."))
        self.volumeSliderLabel.setText(_translate("vapoursonic", "Volume"))
        self.playingAlbumArt.setText(_translate("vapoursonic", "playingAlbumArt"))
        self.currentPlayingLabel.setText(_translate("vapoursonic", "Not Playing"))
        self.trackArtistName.setText(_translate("vapoursonic", "No Artist"))
        self.trackProgressIndicator.setText(_translate("vapoursonic", "00:00/00:00"))
        self.prevTrack.setText(_translate("vapoursonic", "..."))
        self.playPause.setText(_translate("vapoursonic", "..."))
        self.nextTrack.setText(_translate("vapoursonic", "..."))
        self.stop.setText(_translate("vapoursonic", "..."))
        self.menuFile.setTitle(_translate("vapoursonic", "File"))
        self.actionConnect.setText(_translate("vapoursonic", "Disconnect"))
        self.actionExit.setText(_translate("vapoursonic", "Exit"))

from vapoursonic.playqueueview import PlayQueueView
