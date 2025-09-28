#!/usr/bin/env -S uv run --script
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QWidget,
)


@dataclass
class Demo:
    button_name: str
    root_path: str
    app_full_path: str


class DemoRunner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyNGL Demos")
        self._find_executables()
        self.load_ui()

        # Create a scroll area and replace the demo_list placeholder
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        parent_layout = self.demo_list.parentWidget().layout()
        parent_layout.replaceWidget(self.demo_list, scroll_area)
        scroll_area.setWidget(self.demo_list)

        # now add a new button for each executable found
        layout = self.demo_list.layout()
        self.button_group = QButtonGroup(self)
        self.button_group.buttonToggled.connect(self.on_demo_toggled)

        for demo in self.executables:
            button = QPushButton(demo.button_name)
            button.setObjectName(demo.button_name)
            button.setCheckable(True)
            button.setFlat(True)
            button.setStyleSheet("QPushButton { text-align: left; padding: 5px; }")
            self.button_group.addButton(button)
            layout.addWidget(button)

        if self.button_group.buttons():
            self.button_group.buttons()[0].setChecked(True)

    def _find_executables(self):
        root = Path.cwd()
        exclude_dirs = {".venv", ".git", "__pycache__"}
        exclude_stems = {__name__}

        def walk(root: Path):
            for p in root.iterdir():
                if p.is_dir():
                    if p.name in exclude_dirs:
                        continue
                    yield from walk(p)
                elif p.suffix == ".py":
                    if (
                        p.stem in exclude_stems
                        or p.name == f"{next(iter(exclude_stems))}.py"
                    ):
                        continue
                    if os.access(p, os.X_OK):
                        yield p

        self.executables = []
        for p in walk(root):
            if p.stem == "RunDemos":
                continue
            demo = Demo(
                button_name=p.parent.name,
                root_path=str(p.parent),
                app_full_path=str(p),
            )
            self.executables.append(demo)

    def load_ui(self) -> None:
        """Load the UI from a .ui file and set up the connections."""
        loader = QUiLoader()
        ui_file = QFile("DemoUI.ui")
        ui_file.open(QFile.ReadOnly)
        # Load the UI into `self` as the parent
        loaded_ui = loader.load(ui_file, self)
        self.setCentralWidget(loaded_ui)
        # add all children with object names to `self`
        for child in loaded_ui.findChildren(QWidget):
            name = child.objectName()

            if name:
                setattr(self, name, child)
        ui_file.close()
        self.run_demo.clicked.connect(self.on_demo_clicked)

    def on_demo_clicked(self):
        if self.active_demo:
            # run the full app using subporocess
            subprocess.run(
                [self.active_demo.app_full_path],
                shell=True,
                cwd=self.active_demo.root_path,
            )

    def _load_image(self, path):
        # find any png files in the root path
        image_path = Path(path)
        for file in image_path.glob("*.png"):
            pixmap = QPixmap(file)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap)
                break

    def _load_readme(self, path):
        try:
            readme_path = Path(path) / "README.md"
            print(readme_path.read_text())
            self.demo_text.setMarkdown(readme_path.read_text())
        except FileNotFoundError:
            print("README.md not found")

    def on_demo_toggled(self, button, checked):
        if checked:
            button_name = button.objectName()
            for demo in self.executables:
                if demo.button_name == button_name:
                    self.active_demo = demo
                    self._load_image(self.active_demo.root_path)
                    self._load_readme(self.active_demo.root_path)
                    break

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            ...


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = DemoRunner()
    demo.resize(800, 600)
    demo.show()
    sys.exit(app.exec())
