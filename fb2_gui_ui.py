from PyQt6.QtCore import QMetaObject, QRect, QSize, Qt
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFormLayout, QFrame, QGridLayout, QGroupBox, 
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu, QMenuBar, 
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem, QSplitter, 
    QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, 
    QToolBar, QVBoxLayout, QWidget
)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 800)
        
        self.centralwidget = QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        
        # Main splitter between controls and results
        self.splitter = QSplitter(parent=self.centralwidget)
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")
        
        # Top widget with controls
        self.widgetTop = QWidget(parent=self.splitter)
        self.widgetTop.setObjectName("widgetTop")
        
        self.verticalLayoutTop = QVBoxLayout(self.widgetTop)
        self.verticalLayoutTop.setObjectName("verticalLayoutTop")
        
        # Database info
        self.groupBoxDatabase = QGroupBox(parent=self.widgetTop)
        self.groupBoxDatabase.setObjectName("groupBoxDatabase")
        self.groupBoxDatabase.setTitle("Database Information")
        
        self.formLayoutDatabase = QFormLayout(self.groupBoxDatabase)
        self.formLayoutDatabase.setObjectName("formLayoutDatabase")
        
        self.labelDatabase = QLabel(parent=self.groupBoxDatabase)
        self.labelDatabase.setObjectName("labelDatabase")
        self.labelDatabase.setText("Database: Not selected")
        
        self.labelBookCount = QLabel(parent=self.groupBoxDatabase)
        self.labelBookCount.setObjectName("labelBookCount")
        self.labelBookCount.setText("Total books: 0")
        
        self.formLayoutDatabase.setWidget(0, QFormLayout.ItemRole.LabelRole, self.labelDatabase)
        self.formLayoutDatabase.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelBookCount)
        
        self.verticalLayoutTop.addWidget(self.groupBoxDatabase)
        
        # Processing controls
        self.groupBoxProcessing = QGroupBox(parent=self.widgetTop)
        self.groupBoxProcessing.setObjectName("groupBoxProcessing")
        self.groupBoxProcessing.setTitle("Process Archives")
        
        self.gridLayoutProcessing = QGridLayout(self.groupBoxProcessing)
        self.gridLayoutProcessing.setObjectName("gridLayoutProcessing")
        
        self.labelArchivesDir = QLabel(parent=self.groupBoxProcessing)
        self.labelArchivesDir.setObjectName("labelArchivesDir")
        self.labelArchivesDir.setText("Archives Directory: Not selected")
        
        self.buttonSelectArchivesDir = QPushButton(parent=self.groupBoxProcessing)
        self.buttonSelectArchivesDir.setObjectName("buttonSelectArchivesDir")
        self.buttonSelectArchivesDir.setText("Select Directory")
        
        self.checkBoxForceReprocess = QCheckBox(parent=self.groupBoxProcessing)
        self.checkBoxForceReprocess.setObjectName("checkBoxForceReprocess")
        self.checkBoxForceReprocess.setText("Force reprocess all archives")
        
        self.buttonProcess = QPushButton(parent=self.groupBoxProcessing)
        self.buttonProcess.setObjectName("buttonProcess")
        self.buttonProcess.setText("Process Archives")
        
        self.progressBar = QProgressBar(parent=self.groupBoxProcessing)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setValue(0)
        
        self.textLog = QTextEdit(parent=self.groupBoxProcessing)
        self.textLog.setObjectName("textLog")
        self.textLog.setReadOnly(True)
        
        self.gridLayoutProcessing.addWidget(self.labelArchivesDir, 0, 0, 1, 2)
        self.gridLayoutProcessing.addWidget(self.buttonSelectArchivesDir, 1, 0, 1, 1)
        self.gridLayoutProcessing.addWidget(self.checkBoxForceReprocess, 1, 1, 1, 1)
        self.gridLayoutProcessing.addWidget(self.buttonProcess, 2, 0, 1, 2)
        self.gridLayoutProcessing.addWidget(self.progressBar, 3, 0, 1, 2)
        self.gridLayoutProcessing.addWidget(self.textLog, 4, 0, 1, 2)
        
        self.verticalLayoutTop.addWidget(self.groupBoxProcessing)
        
        # Bottom widget with results
        self.widgetBottom = QWidget(parent=self.splitter)
        self.widgetBottom.setObjectName("widgetBottom")
        
        self.verticalLayoutBottom = QVBoxLayout(self.widgetBottom)
        self.verticalLayoutBottom.setObjectName("verticalLayoutBottom")
        
        # Search controls
        self.groupBoxSearch = QGroupBox(parent=self.widgetBottom)
        self.groupBoxSearch.setObjectName("groupBoxSearch")
        self.groupBoxSearch.setTitle("Search Database")
        
        self.horizontalLayoutSearch = QHBoxLayout(self.groupBoxSearch)
        self.horizontalLayoutSearch.setObjectName("horizontalLayoutSearch")
        
        self.lineEditSearch = QLineEdit(parent=self.groupBoxSearch)
        self.lineEditSearch.setObjectName("lineEditSearch")
        self.lineEditSearch.setPlaceholderText("Enter search terms...")
        
        self.buttonSearch = QPushButton(parent=self.groupBoxSearch)
        self.buttonSearch.setObjectName("buttonSearch")
        self.buttonSearch.setText("Search")
        
        self.horizontalLayoutSearch.addWidget(self.lineEditSearch)
        self.horizontalLayoutSearch.addWidget(self.buttonSearch)
        
        self.verticalLayoutBottom.addWidget(self.groupBoxSearch)
        
        # Results table
        self.tableResults = QTableWidget(parent=self.widgetBottom)
        self.tableResults.setObjectName("tableResults")
        
        # Set up columns
        self.tableResults.setColumnCount(8)
        self.tableResults.setHorizontalHeaderLabels([
            "ID", "Title", "Author", "Year", "Publisher", "Archive", "Path", "Size"
        ])
        
        header = self.tableResults.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Author
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Year
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Publisher
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Archive
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Path
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Size
        
        self.verticalLayoutBottom.addWidget(self.tableResults)
        
        # Add the splitter to main layout
        self.verticalLayout.addWidget(self.splitter)
        
        # Set up menus
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.menubar = QMenuBar(parent=MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1000, 22))
        
        self.menuFile = QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuFile.setTitle("File")
        
        MainWindow.setMenuBar(self.menubar)
        
        self.statusbar = QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        self.actionOpen_Database = self.menuFile.addAction("Open Database")
        self.actionCreate_New_Database = self.menuFile.addAction("Create New Database")
        self.menuFile.addSeparator()
        self.actionExit = self.menuFile.addAction("Exit")
        
        self.menubar.addAction(self.menuFile.menuAction())
        
        # Set up splitter sizes
        self.splitter.setSizes([400, 400])
        
        QMetaObject.connectSlotsByName(MainWindow)