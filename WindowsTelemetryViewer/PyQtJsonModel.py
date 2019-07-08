__license__ = "MIT"

__copyright__ = r"""
MIT License

Copyright (c) 2017 Gregor Engberding

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import json

from PySide2.QtCore import QAbstractItemModel, QAbstractListModel, QByteArray, QDataStream, QJsonParseError, QJsonValue, QMimeData, QModelIndex, Qt
from PySide2.QtWidgets import QApplication, QFileDialog


class QJsonTreeItem(object):
	def __init__(self, parent=None):

		self.mParent = parent
		self.mChilds = []
		self.mType = None
		self.mValue = None

	def appendChild(self, item):
		self.mChilds.append(item)

	def child(self, row: int):
		return self.mChilds[row]

	def parent(self):
		return self.mParent

	def childCount(self):
		return len(self.mChilds)

	def row(self):
		if self.mParent is not None:
			return self.mParent.mChilds.index(self)
		return 0

	def setKey(self, key: str):
		self.mKey = key

	def setValue(self, value: str):
		self.mValue = value

	def setType(self, type: QJsonValue.Type):
		self.mType = type

	def key(self):
		return self.mKey

	def value(self):
		return self.mValue

	def type(self):
		return self.mType

	def load(self, value, parent=None):

		rootItem = QJsonTreeItem(parent)
		rootItem.setKey("root")
		jsonType = None

		jsonType = value.__class__.__name__

		if isinstance(value, dict):
			# process the key/value pairs
			for key in value:
				v = value[key]
				child = self.load(v, rootItem)
				child.setKey(key)
				child.setType(v.__class__.__name__)
				rootItem.appendChild(child)

		elif isinstance(value, list):
			# process the values in the list
			for i, v in enumerate(value):
				child = self.load(v, rootItem)
				child.setKey(str(i))
				child.setType(v.__class__)
				rootItem.appendChild(child)

		else:
			# value is processed
			rootItem.setValue(value)
			try:
				rootItem.setType(value.type())
			except AttributeError:
				if jsonType is not None:
					rootItem.setType(jsonType)
				else:
					rootItem.setType(value.__class__)

		return rootItem


class QJsonModel(QAbstractItemModel):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.mRootItem = QJsonTreeItem()
		self.mHeaders = ["key", "value", "type"]

	def load(self, fileName):
		if fileName is None or fileName is False:
			return False

		with open(fileName, "rb") as file:
			if file is None:
				return False
			else:
				jsonTxt = file.read()
				self.loadJson(jsonTxt)

	def loadJson(self, json):
		error = QJsonParseError()
		return self.loadDict(QJsonDocument.fromJson(json, error))

	def loadDict(self, dic):
		self.mDocument = dic
		if self.mDocument is not None:
			self.beginResetModel()
			if isinstance(self.mDocument, list):
				self.mRootItem.load(list(self.mDocument))
			else:
				self.mRootItem = self.mRootItem.load(self.mDocument)
			self.endResetModel()

			return True

		# print("QJsonModel: error loading Json")
		return False

	def data(self, index: QModelIndex, role: int = ...):
		if not index.isValid():
			return None

		item = index.internalPointer()
		col = index.column()

		if role == Qt.DisplayRole:
			if col == 0:
				return str(item.key())
			elif col == 1:
				return str(item.value())
			elif col == 2:
				return str(item.type())

		return None

	def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
		if role != Qt.DisplayRole:
			return None

		if orientation == Qt.Horizontal:
			return self.mHeaders[section]

		return QVariant()

	def index(self, row: int, column: int, parent: QModelIndex = ...):
		if not self.hasIndex(row, column, parent):
			return QModelIndex()

		if not parent.isValid():
			parentItem = self.mRootItem
		else:
			parentItem = parent.internalPointer()
		try:
			childItem = parentItem.child(row)
			return self.createIndex(row, column, childItem)
		except IndexError:
			return QModelIndex()

	def parent(self, index: QModelIndex):
		if not index.isValid():
			return QModelIndex()

		childItem = index.internalPointer()
		parentItem = childItem.parent()

		if parentItem == self.mRootItem:
			return QModelIndex()

		return self.createIndex(parentItem.row(), 0, parentItem)

	def rowCount(self, parent: QModelIndex = ...):
		if parent.column() > 0:
			return 0
		if not parent.isValid():
			parentItem = self.mRootItem
		else:
			parentItem = parent.internalPointer()

		return parentItem.childCount()

	def columnCount(self, parent: QModelIndex = ...):
		return 3
