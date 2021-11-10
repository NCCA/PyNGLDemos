#!/usr/bin/env python
try : # support either PyQt5 or 6
  from PyQt5.QtGui import QMainWindow,QSurfaceFormat
  from PyQt5.QtWidgets import QApplication
  from PyQt5.QtCore import *
  from PyQt5 import uic
  PyQtVersion = 5
except ImportError:
  print('trying Qt6')
  from PyQt6.QtGui import QSurfaceFormat
  from PyQt6.QtWidgets import QApplication,QMainWindow
  from PyQt6.QtCore import QEvent,Qt
  from PyQt6 import uic
  PyQtVersion = 6

import sys
from NGLScene import NGLScene
    

class MainWindow(QMainWindow) :
  
  def __init__(self, parent=None):
    super(QMainWindow, self).__init__(parent)
    uic.loadUi('MainWindow.ui', self) # Load the .ui file
    glWidget=NGLScene(self)
    self.mainWindowGridLayout.addWidget(glWidget,0,0,2,1)
    self.wireframe.clicked.connect(glWidget.toggleWireframe)
    self.objectSelection.currentTextChanged.connect(glWidget.setModel)
    # it's simple to do a 1-1 mapping of methods
    self.rotationX.valueChanged.connect(glWidget.setRotationX)
    self.rotationY.valueChanged.connect(glWidget.setRotationY)
    self.rotationZ.valueChanged.connect(glWidget.setRotationZ)
    # however we can use a lambda to add decoration to the function
    self.scaleX.valueChanged.connect( lambda : glWidget.setScale(self.scaleX,'x'))
    self.scaleY.valueChanged.connect( lambda : glWidget.setScale(self.scaleY,'y'))
    self.scaleZ.valueChanged.connect( lambda : glWidget.setScale(self.scaleZ,'z'))

    self.positionX.valueChanged.connect( lambda : glWidget.setPosition(self.positionX,'x'))
    self.positionY.valueChanged.connect( lambda : glWidget.setPosition(self.positionY,'y'))
    self.positionZ.valueChanged.connect( lambda : glWidget.setPosition(self.positionZ,'z'))
    self.colour.clicked.connect(glWidget.setColour)

  if PyQtVersion == 5 :
    def keyPressEvent(self, event) :
      key=event.key()
      if key==Qt.Key_Escape :
        exit()
      self.update()
  ##############################################################################
  # Qt6 
  ##############################################################################
  else : # Qt6 Versions
    def keyPressEvent(self, event) :
        key=event.key()
        if key==Qt.Key.Key_Escape :
          exit()
        self.update()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  format=QSurfaceFormat()
  format.setSamples(4) 
  format.setMajorVersion(4) 
  format.setMinorVersion(1) 
  print(format.profile())
  if PyQtVersion == 5 :
    format.setProfile(QSurfaceFormat.CoreProfile) 
  else :
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile) 

  # now set the depth buffer to 24 bits
  format.setDepthBufferSize(24) 
  # set that as the default format for all windows
  QSurfaceFormat.setDefaultFormat(format) 

  window = MainWindow()
  window.resize(1024,720)
  window.show()
  if PyQtVersion == 5 :
    sys.exit(app.exec_())
  else :
    sys.exit(app.exec())
