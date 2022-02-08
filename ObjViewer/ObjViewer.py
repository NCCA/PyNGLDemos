#!/usr/bin/env python
try:  # support either PyQt5 or 6
    from PyQt5.QtCore import *
    from PyQt5.QtGui import QOpenGLWindow, QSurfaceFormat
    from PyQt5.QtWidgets import QApplication

    PyQtVersion = 5
except ImportError:
    print("trying Qt6")
    from PyQt6.QtCore import QEvent, Qt
    from PyQt6.QtGui import QSurfaceFormat
    from PyQt6.QtOpenGL import QOpenGLWindow
    from PyQt6.QtWidgets import QApplication

    PyQtVersion = 6

import argparse
import sys

from OpenGL.GL import *
from pyngl import *


class MainWindow(QOpenGLWindow):
    def __init__(self, oname, tname, parent=None):
        super(QOpenGLWindow, self).__init__(parent)
        self.mouseGlobalTX = Mat4()
        self.width = int(1024)
        self.height = int(720)
        self.setTitle("pyNGL demo")
        self.spinXFace = int(0)
        self.spinYFace = int(0)
        self.rotate = False
        self.translate = False

    def wheelEvent(self, event):
        numPixels = event.pixelDelta()
        if numPixels.x() > 0:
            self.modelPos.m_z += self.ZOOM

        elif numPixels.x() < 0:
            self.modelPos.m_z -= self.ZOOM
        if numPixels.y() > 0:
            self.modelPos.m_x += self.ZOOM

        elif numPixels.y() < 0:
            self.modelPos.m_x -= self.ZOOM

        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            exit()
        elif key == Qt.Key.Key_W:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        elif key == Qt.Key.Key_S:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        elif key == Qt.Key.Key_Space:
            self.spinXFace = 0
            self.spinYFace = 0
            self.modelPos.set(Vec3.zero())
        elif key == Qt.Key.Key_B:
            self.showBBox ^= True
        elif key == Qt.Key.Key_P:
            self.showBSphere ^= True
        self.update()

    # todo try and capture Mac gestures
    def nativeEvent(self, event, message):
        retval, result = super(QOpenGLWindow, self).nativeEvent(event, message)
        return retval, result


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Mesh and Texture options")
    parser.add_argument(
        "--obj",
        "-o",
        nargs="?",
        const="",
        default="",
        type=str,
        help="Obj mesh to load",
    )
    parser.add_argument(
        "--tex", "-t", nargs="?", const="", default="", type=str, help="texture to load"
    )

    args = parser.parse_args()
    if args.obj:
        oname = args.obj
    else:
        oname = "Helix.obj"
    if args.tex:
        tname = args.tex
    else:
        tname = "helix_base.tif"

    app = QApplication(sys.argv)
    format = QSurfaceFormat()
    format.setSamples(4)
    format.setMajorVersion(4)
    format.setMinorVersion(1)
    print(format.profile())
    if PyQtVersion == 5:
        format.setProfile(QSurfaceFormat.CoreProfile)
    else:
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)

    # now set the depth buffer to 24 bits
    format.setDepthBufferSize(24)
    # set that as the default format for all windows
    QSurfaceFormat.setDefaultFormat(format)

    window = MainWindow(oname, tname)
    window.setFormat(format)
    window.resize(1024, 720)
    window.show()
    if PyQtVersion == 5:
        sys.exit(app.exec_())
    else:
        sys.exit(app.exec())
