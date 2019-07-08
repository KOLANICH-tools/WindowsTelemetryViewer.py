import sys

from plumbum import cli

from PySide2.QtWidgets import QApplication

from . import TelemetryViewerGUI


class App(cli.Application):
	def main(self, f: cli.ExistingFile = None):
		app = QApplication(sys.argv)
		w = TelemetryViewerGUI()
		w.show()
		if f is not None:
			w.loadTelemetry(f)
		else:
			w.openTelemetry()
		sys.exit(app.exec_())


if __name__ == "__main__":
	App.run()
