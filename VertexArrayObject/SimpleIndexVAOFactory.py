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

import sys

from OpenGL.GL import *
from pyngl import *


class MainWindow(QOpenGLWindow):
    def __init__(self, parent=None):
        super(QOpenGLWindow, self).__init__(parent)
        self.mouseGlobalTX = Mat4()
        self.width = int(1024)
        self.height = int(720)
        self.setTitle("SimpleIndexedVAO Python")
        self.spinXFace = int(0)
        self.spinYFace = int(0)
        self.rotate = False
        self.translate = False
        self.origX = int(0)
        self.origY = int(0)
        self.origXPos = int(0)
        self.origYPos = int(0)
        self.INCREMENT = 0.01
        self.ZOOM = 0.1
        self.modelPos = Vec3()
        self.view = Mat4()
        self.project = Mat4()
        self.vao = None

    def initializeGL(self):
        self.makeCurrent()
        NGLInit.initialize()
        glClearColor(0.4, 0.4, 0.4, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        ShaderLib.loadShader(
            "Colour",
            "../shaders/ColourVertex.glsl",
            "../shaders/ColourFragment.glsl",
            ErrorExit.OFF,
        )
        ShaderLib.use("Colour")

        self.view = lookAt(Vec3(0, 1, 2), Vec3.zero(), Vec3.up())
        self.project = perspective(
            45.0, float(self.width) / float(self.height), 0.05, 350.0
        )
        self.buildVAO()

    def buildVAO(self):
        vertAndColour = VectorVec3(
            [
                Vec3(-0.26286500, 0.0000000, 0.42532500),
                Vec3(1.0, 0.0, 0.0),
                Vec3(0.26286500, 0.0000000, 0.42532500),
                Vec3(1.0, 0.55, 0.0),
                Vec3(-0.26286500, 0.0000000, -0.42532500),
                Vec3(1.0, 0.0, 1.0),
                Vec3(0.26286500, 0.0000000, -0.42532500),
                Vec3(0.0, 1.0, 0.0),
                Vec3(0.0000000, 0.42532500, 0.26286500),
                Vec3(0.0, 0.0, 1.0),
                Vec3(0.0000000, 0.42532500, -0.26286500),
                Vec3(0.29, 0.51, 0.0),
                Vec3(0.0000000, -0.42532500, 0.26286500),
                Vec3(0.5, 0.0, 0.5),
                Vec3(0.0000000, -0.42532500, -0.26286500),
                Vec3(1.0, 1.0, 1.0),
                Vec3(0.42532500, 0.26286500, 0.0000000),
                Vec3(0.0, 1.0, 1.0),
                Vec3(-0.42532500, 0.26286500, 0.0000000),
                Vec3(0.0, 0.0, 0.0),
                Vec3(0.42532500, -0.26286500, 0.0000000),
                Vec3(0.12, 0.56, 1.0),
                Vec3(-0.42532500, -0.26286500, 0.0000000),
                Vec3(0.86, 0.08, 0.24),
            ]
        )

        indices = VectorUint(
            [
                0,
                6,
                1,
                0,
                11,
                6,
                1,
                4,
                0,
                1,
                8,
                4,
                1,
                10,
                8,
                2,
                5,
                3,
                2,
                9,
                5,
                2,
                11,
                9,
                3,
                7,
                2,
                3,
                10,
                7,
                4,
                8,
                5,
                4,
                9,
                0,
                5,
                8,
                3,
                5,
                9,
                4,
                6,
                10,
                1,
                6,
                11,
                7,
                7,
                10,
                6,
                7,
                11,
                2,
                8,
                10,
                3,
                9,
                11,
                0,
            ]
        )

        self.vao = VAOFactory.createVAO(simpleIndexVAO, GL_TRIANGLES)
        self.vao.bind()
        self.vao.setData(
            len(vertAndColour) * Vec3.sizeof(), vertAndColour, len(indices), indices
        )
        self.vao.setVertexAttributePointer(0, 3, GL_FLOAT, 24, 0)
        self.vao.setVertexAttributePointer(1, 3, GL_FLOAT, 24, 3)

        self.vao.setNumIndices(len(indices))
        self.vao.unbind()

    def loadMatricesToShader(self):
        ShaderLib.use("Colour")

        ShaderLib.setUniform("MVP", self.project * self.view * self.mouseGlobalTX)

    def paintGL(self):
        try:
            self.makeCurrent()
            glViewport(0, 0, self.width, self.height)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            rotX = Mat4()
            rotY = Mat4()
            rotX.rotateX(self.spinXFace)
            rotY.rotateY(self.spinYFace)
            self.mouseGlobalTX = rotY * rotX
            self.mouseGlobalTX.m_30 = self.modelPos.m_x
            self.mouseGlobalTX.m_31 = self.modelPos.m_y
            self.mouseGlobalTX.m_32 = self.modelPos.m_z
            self.loadMatricesToShader()
            self.vao.bind()
            self.vao.draw()
            self.vao.unbind()
        except OpenGL.error.GLError:
            print("error")

    def resizeGL(self, w, h):
        self.width = int(w * self.devicePixelRatio())
        self.height = int(h * self.devicePixelRatio())
        self.project = perspective(45.0, float(w) / h, 0.05, 350.0)

    if PyQtVersion == 5:

        def keyPressEvent(self, event):
            key = event.key()
            if key == Qt.Key_Escape:
                exit()
            elif key == Qt.Key_W:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            elif key == Qt.Key_S:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            elif key == Qt.Key_Space:
                self.spinXFace = 0
                self.spinYFace = 0
                self.modelPos.set(Vec3.zero())
            elif key == Qt.Key_L:
                self.transformLight ^= True
            self.update()

        def mouseMoveEvent(self, event):
            if self.rotate and event.buttons() == Qt.LeftButton:

                diffx = int(event.x() - self.origX)
                diffy = int(event.y() - self.origY)
                self.spinXFace += int(0.5 * diffy)
                self.spinYFace += int(0.5 * diffx)
                self.origX = event.x()
                self.origY = event.y()
                self.update()
            elif self.translate and event.buttons() == Qt.RightButton:

                diffX = int(event.x() - self.origXPos)
                diffY = int(event.y() - self.origYPos)
                self.origXPos = event.x()
                self.origYPos = event.y()
                self.modelPos.m_x += self.INCREMENT * diffX
                self.modelPos.m_y -= self.INCREMENT * diffY
                self.update()

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.origX = event.x()
                self.origY = event.y()
                self.rotate = True

            elif event.button() == Qt.RightButton:
                self.origXPos = event.x()
                self.origYPos = event.y()
                self.translate = True

        def mouseReleaseEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.rotate = False

            elif event.button() == Qt.RightButton:
                self.translate = False

        def wheelEvent(self, event):
            numPixels = event.pixelDelta()

            if numPixels.x() > 0:
                self.modelPos.m_z += self.ZOOM

            elif numPixels.x() < 0:
                self.modelPos.m_z -= self.ZOOM
            self.update()

    ##############################################################################
    # Qt6
    ##############################################################################
    else:  # Qt6 Versions

        def mousePressEvent(self, event):
            pos = event.position()
            if event.button() == Qt.MouseButton.LeftButton:
                self.origX = pos.x()
                self.origY = pos.y()
                self.rotate = True

            elif event.button() == Qt.MouseButton.RightButton:
                self.origXPos = pos.x()
                self.origYPos = pos.y()
                self.translate = True

        def mouseMoveEvent(self, event):
            if self.rotate and event.buttons() == Qt.MouseButton.LeftButton:
                pos = event.position()
                diffx = int(pos.x() - self.origX)
                diffy = int(pos.y() - self.origY)
                self.spinXFace += int(0.5 * diffy)
                self.spinYFace += int(0.5 * diffx)
                self.origX = pos.x()
                self.origY = pos.y()
                self.update()
            elif self.translate and event.buttons() == Qt.MouseButton.RightButton:
                pos = event.position()
                diffX = int(pos.x() - self.origXPos)
                diffY = int(pos.y() - self.origYPos)
                self.origXPos = pos.x()
                self.origYPos = pos.y()
                self.modelPos.m_x += self.INCREMENT * diffX
                self.modelPos.m_y -= self.INCREMENT * diffY
                self.update()

        def mouseReleaseEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.rotate = False

            elif event.button() == Qt.MouseButton.RightButton:
                self.translate = False

        def wheelEvent(self, event):
            numPixels = event.pixelDelta()

            if numPixels.x() > 0:
                self.modelPos.m_z += self.ZOOM

            elif numPixels.x() < 0:
                self.modelPos.m_z -= self.ZOOM
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
            elif key == Qt.Key.Key_L:
                self.transformLight ^= True
            self.update()


if __name__ == "__main__":
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

    window = MainWindow()
    window.setFormat(format)
    window.resize(1024, 720)
    window.show()
    if PyQtVersion == 5:
        sys.exit(app.exec_())
    else:
        sys.exit(app.exec())
