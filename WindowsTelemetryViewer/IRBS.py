from pathlib import Path


class IRBS:
	def __init__(self, path: Path):
		raise NotImplementedError()

	def __iter__(self):
		raise NotImplementedError()


class IRBSItem:
	__slots__ = ("obj",)

	def __init__(self, obj):
		self.obj = obj

	@property
	def json(self):
		raise NotImplementedError()

	@property
	def index(self):
		raise NotImplementedError()

	@property
	def unkn3(self):
		raise NotImplementedError()

	@property
	def unkn4(self):
		raise NotImplementedError()


try:
	raise ImportError  # performance is the same, preferring our Kaitai parser
	import struct

	from rbs_parser import RBSFile

	class Bluec0reRBSItem(IRBSItem):
		__slots__ = ()

		@property
		def json(self):
			return self.obj.uncompressed.decode("utf-8").splitlines()

		@property
		def index(self):
			return struct.unpack("<I", self.obj.unknown[4:8])[0]

		@property
		def unkn3(self):
			return self.obj.maybe_type

		@property
		def unkn4(self):
			return struct.unpack("<H", self.obj.unknown2)[0] if len(self.obj.unknown2) > 1 else self.obj.unknown2[0]

	class Bluec0reRBS(IRBS):
		def __init__(self, path: Path):
			self.parsed = RBSFile(str(path))

		def __iter__(self):
			with self.parsed:
				yield from map(Bluec0reRBSItem, self.parsed)

	SelectedRBS = Bluec0reRBS
except ImportError:
	from .kaitai.windows_diagnostics_framework_rbs import *

	class KaitaiRBSItem(IRBSItem):
		__slots__ = ()

		@property
		def json(self):
			return self.obj.data.value.splitlines()

		@property
		def index(self):
			return self.obj.header.index

		@property
		def unkn3(self):
			return self.obj.header.unkn3

		@property
		def unkn4(self):
			return self.obj.header.unkn4

	class KaitaiRBS(IRBS):
		def __init__(self, path: Path):
			self.parsed = WindowsDiagnosticsFrameworkRbs.from_file(str(path))

		def __iter__(self):
			yield from map(KaitaiRBSItem, self.parsed.reserved_size.items.items)

	SelectedRBS = KaitaiRBS
