import os
import sys
from pathlib import Path

from PySide2.QtCore import QAbstractTableModel, QEvent, QObject, QSize, Qt
from PySide2.QtGui import QIcon, QWindow
from PySide2.QtWidgets import QBoxLayout, QCheckBox, QDockWidget, QDoubleSpinBox, QErrorMessage, QFileDialog, QGridLayout, QHeaderView, QLabel, QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QTableView, QTableWidget, QTableWidgetItem, QTextEdit, QWidget, QTreeView

from .IRBS import SelectedRBS
from .PyQtJsonModel import QJsonTreeItem, QJsonModel
from .TableWidget import TableWidget

try:
	import locale

	from dateutil import tz
	from dateutil.parser import parse as parseTime

	locale.setlocale(locale.LC_TIME, "")
	import time

	tz = tz.tzlocal()

	def transformTimeIntoLocal(timeStrFromJSON: str) -> str:
		t = parseTime(timeStrFromJSON).astimezone(tz)
		tStr = t.strftime("%a, %x %X").encode("CP1252").decode("CP1251")  # WTF?
		return tStr


except ImportError:

	def transformTimeIntoLocal(timeStrFromJSON: str) -> str:
		return timeStrFromJSON


try:
	import ujson as json

	def parseJSON(s: str) -> dict:
		return json.loads(s)


except ImportError:
	import json
	from collections import OrderedDict

	def parseJSON(s: str) -> dict:
		return json.loads(s, object_pairs_hook=OrderedDict)


class TelemetryViewerGUI(QMainWindow):
	def __init__(self):
		super().__init__()
		title = "Telemetry Viewer"
		self.setWindowTitle(title)
		if sys.platform == "win32":
			import ctypes

			try:
				ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(title.replace(" ", "_"))
			except BaseException:
				pass
		self.icon = QIcon()
		iconPath = Path(__file__).parent / "icon.ico"
		self.icon.addFile(str(iconPath), QSize(64, 64))
		self.setWindowIcon(self.icon)

		self.setAcceptDrops(True)

		self.fileDlg = QFileDialog(self, Qt.WindowFlags(0))

		try:
			parentDir = str(Path(os.environ["ProgramData"]) / "Microsoft" / "Diagnosis")
		except BaseException:
			parentDir = "."

		self.fileDlg.setDirectory(parentDir)

		def callback(_, rowNo):
			#self.ar.setText(json.dumps(self.indexed[rowNo], indent="\t"))
			self.model.loadDict(self.indexed[rowNo])

		self.table = TableWidget(("#", "subIdx", "idx", "unkn3", "unkn4", "name", "time"), self, callback)

		#self.ar = QScrollArea(self)
		#self.ar = QTextEdit(self)
		self.ar = QTreeView()
		self.header = self.ar.header()

		self.model = QJsonModel()
		self.ar.setModel(self.model)
		for i in range(3):
			self.header.setSectionResizeMode(QHeaderView.ResizeToContents)

		#self.ar.setFontFamily("monospace")
		#self.ar.setReadOnly(True)
		#self.ar.acceptRichText
		#.dropEvent
		#wordWrapMode

		dockableWindowsFeatures = QDockWidget.DockWidgetFeatures(QDockWidget.AllDockWidgetFeatures & ~QDockWidget.DockWidgetClosable)

		self.JSONWindow = QDockWidget("JSON", self)
		self.JSONWindow.setFeatures(dockableWindowsFeatures)
		self.addDockWidget(Qt.RightDockWidgetArea, self.JSONWindow)  # l
		self.JSONWindow.setWidget(self.ar)

		self.tableWindow = QDockWidget("Table", self)
		self.tableWindow.setFeatures(dockableWindowsFeatures)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.tableWindow)
		self.tableWindow.setWidget(self.table)

		#self.openTelemetryBtn = QPushButton("Open telemetry", self)
		#self.openTelemetryBtn.clicked.connect(self.openTelemetry)

		self.indexed = {}

	telemetryFileMask = "Windows Diagnostics Framework (*.rbs)"

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, evt):
		urls = evt.mimeData().urls()
		if len(urls) != 1:
			errMsg = QErrorMessage()
			errMsg.showMessage("Drop exactly single rbs file!")
		else:
			self.loadTelemetry(urls[0].toLocalFile())

	def openTelemetry(self) -> None:
		fns = self.fileDlg.getOpenFileName(self, "Load telemetry data file", None, self.__class__.telemetryFileMask)
		if fns[0]:
			self.loadTelemetry(fns[0])

	def loadTelemetry(self, f: str) -> None:
		self.table.clear()
		parsed = SelectedRBS(f)
		self.indexed = {}
		i = 0
		for j, item in enumerate(parsed):
			#repr(item.header.unkn3)  # bluec0re suspects it is the type
			for subIndex, subItemText in enumerate(item.json):
				jso = parseJSON(subItemText)
				self.indexed[i] = jso

				self.table.appendRow(i - 1, (j, subIndex, item.index, item.unkn3, item.unkn4, jso["name"], transformTimeIntoLocal(jso["time"])))
				i += 1
		del parsed
		self.table.table.resizeColumnsToContents()
		if i:
			self.table.table.setCurrentIndex(self.table.table.model().index(0, 0))
