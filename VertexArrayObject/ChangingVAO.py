#!/usr/bin/env python
try : # support either PyQt5 or 6
  from PyQt5.QtGui import QOpenGLWindow,QSurfaceFormat
  from PyQt5.QtWidgets import QApplication
  from  PyQt5.QtCore import *
  PyQtVersion = 5
except ImportError:
  print('trying Qt6')
  from PyQt6.QtGui import QSurfaceFormat
  from PyQt6.QtOpenGL import QOpenGLWindow
  from PyQt6.QtWidgets import QApplication
  from PyQt6.QtCore import QEvent,Qt
  PyQtVersion = 6

import sys
from pyngl import *
from OpenGL.GL import *

class MainWindow(QOpenGLWindow) :
  
  def __init__(self, parent=None):
    super(QOpenGLWindow, self).__init__(parent)
    self.mouseGlobalTX=Mat4()
    self.width=1024
    self.height=720
    self.setTitle('Changing VAO')
    self.spinXFace = 0
    self.spinYFace = 0
    self.rotate = False
    self.translate = False
    self.origX = 0
    self.origY = 0
    self.origXPos = 0
    self.origYPos = 0
    self.INCREMENT=0.01
    self.ZOOM=0.1
    self.modelPos=Vec3()
    self.lines=VectorVec3()
    self.view=Mat4()
    self.project=Mat4()


  def initializeGL(self) :
    self.makeCurrent()
    NGLInit.initialize()
    glClearColor( 0.4, 0.4, 0.4, 1.0 ) 
    glEnable( GL_DEPTH_TEST )
    glEnable( GL_MULTISAMPLE )
    ShaderLib.use("nglColourShader");
    ShaderLib.setUniform("Colour",1.0,1.0,1.0,1.0);

    self.view=lookAt(Vec3(0,1,22),Vec3.zero(),Vec3.up())
    self.project=perspective( 45.0, 720.0 / 576.0, 0.05, 350.0 )
    self.vao=VAOFactory.createVAO('simpleVAO',GL_LINES)
    self.text=Text("../fonts/Arial.ttf",18)
    self.text.setScreenSize(self.width,self.height);

    self.startTimer(0)
  
  def paintGL(self):
    try :
      self.makeCurrent()
      glViewport( 0, 0, self.width, self.height )
      glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
      ShaderLib.use('nglColourShader')
      rotX=Mat4();
      rotY=Mat4();
      rotX.rotateX( self.spinXFace );
      rotY.rotateY( self.spinYFace );
      self.mouseGlobalTX = rotY * rotX;
      self.mouseGlobalTX.m_30  = self.modelPos.m_x;
      self.mouseGlobalTX.m_31  = self.modelPos.m_y;
      self.mouseGlobalTX.m_32  = self.modelPos.m_z;
      MVP=self.project*self.view*self.mouseGlobalTX
      ShaderLib.setUniform("MVP",MVP);

      self.vao.bind()
      self.vao.setData(len(self.lines)*Vec3.sizeof(),self.lines)
      # We must do this each time as we change the data.
      self.vao.setVertexAttributePointer(0,3,GL_FLOAT,0,0);
      self.vao.setNumIndices(len(self.lines));
      self.vao.draw();
      self.vao.unbind();

      self.text.setColour(1,1,1);
      text="Data Size %d " %(len(self.lines)/2)
      self.text.renderText(10,700,text );

    except OpenGL.error.GLError :
      print ('error')
      
  def timerEvent(self,event) :
    size=100+int(Random.randomPositiveNumber(12000))
    # clear old list
    self.lines.clear()
    for i in range(0,size*2) :
      self.lines.append(Random.getRandomVec3()*5)
    self.update()

  def resizeGL(self, w,h) :
    self.width=int(w* self.devicePixelRatio())
    self.height=int(h* self.devicePixelRatio())
    self.project=perspective( 45.0, float( w ) / h, 0.05, 350.0 )


  if PyQtVersion == 5 :
    def keyPressEvent(self, event) :
      key=event.key()
      if key==Qt.Key_Escape :
        exit()
      elif key==Qt.Key_W :
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
      elif key==Qt.Key_S :
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
      elif key==Qt.Key_Space :
        self.spinXFace=0
        self.spinYFace=0
        self.modelPos.set(Vec3.zero())
      elif key==Qt.Key_L :
        self.transformLight^=True      
      self.update()

    def mouseMoveEvent(self, event) :
        if self.rotate and event.buttons() == Qt.LeftButton  :
          
          diffx = int(event.x() - self.origX)
          diffy = int(event.y() - self.origY)
          self.spinXFace += int( 0.5 * diffy )
          self.spinYFace += int( 0.5 * diffx )
          self.origX = event.x()
          self.origY = event.y()
          self.update()
        elif  self.translate and event.buttons() == Qt.RightButton :

          diffX   = int( event.x() - self.origXPos )
          diffY   = int( event.y() - self.origYPos )
          self.origXPos = event.x()
          self.origYPos = event.y()
          self.modelPos.m_x += self.INCREMENT * diffX 
          self.modelPos.m_y -= self.INCREMENT * diffY 
          self.update() 


    def mousePressEvent(self,event) :
        if  event.button() == Qt.LeftButton :
          self.origX  = event.x()
          self.origY  = event.y()
          self.rotate = True

        elif  event.button() == Qt.RightButton :
          self.origXPos  = event.x() 
          self.origYPos  = event.y() 
          self.translate = True

    def mouseReleaseEvent(self,event) :
      if  event.button() == Qt.LeftButton :
        self.rotate = False

      elif  event.button() == Qt.RightButton :
        self.translate = False

    def wheelEvent(self,event) :
      numPixels = event.pixelDelta() 

      if  numPixels.x() > 0  :
        self.modelPos.m_z += self.ZOOM

      elif  numPixels.x() < 0 :
        self.modelPos.m_z -= self.ZOOM
      self.update() 

  ##############################################################################
  # Qt6 
  ##############################################################################
  else : # Qt6 Versions

    def mousePressEvent(self,event) :
      pos = event.position()
      if  event.button() == Qt.MouseButton.LeftButton :
        self.origX  = pos.x()
        self.origY  = pos.y()
        self.rotate = True

      elif  event.button() == Qt.MouseButton.RightButton :
        self.origXPos  = pos.x() 
        self.origYPos  = pos.y() 
        self.translate = True
    
    def mouseMoveEvent(self, event) :
      if self.rotate and event.buttons() == Qt.MouseButton.LeftButton  :
        pos=event.position()
        diffx = int(pos.x() - self.origX)
        diffy = int(pos.y() - self.origY)
        self.spinXFace += int( 0.5 * diffy )
        self.spinYFace += int( 0.5 * diffx )
        self.origX = pos.x()
        self.origY = pos.y()
        self.update()
      elif  self.translate and event.buttons() == Qt.MouseButton.RightButton :
        pos=event.position()
        diffX   = int( pos.x() - self.origXPos )
        diffY   = int( pos.y() - self.origYPos )
        self.origXPos = pos.x()
        self.origYPos = pos.y()
        self.modelPos.m_x += self.INCREMENT * diffX 
        self.modelPos.m_y -= self.INCREMENT * diffY 
        self.update() 

    def mouseReleaseEvent(self,event) :
      if  event.button() == Qt.MouseButton.LeftButton :
        self.rotate = False

      elif  event.button() == Qt.MouseButton.RightButton :
        self.translate = False

    def wheelEvent(self,event) :
      numPixels = event.pixelDelta() 

      if  numPixels.x() > 0  :
        self.modelPos.m_z += self.ZOOM

      elif  numPixels.x() < 0 :
        self.modelPos.m_z -= self.ZOOM
      self.update() 

    def keyPressEvent(self, event) :
      key=event.key()
      if key==Qt.Key.Key_Escape :
        exit()
      elif key==Qt.Key.Key_W :
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
      elif key==Qt.Key.Key_S :
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
      elif key==Qt.Key.Key_Space :
        self.spinXFace=0
        self.spinYFace=0
        self.modelPos.set(Vec3.zero())
      elif key==Qt.Key.Key_L :
        self.transformLight^=True      
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
  window.setFormat(format)
  window.resize(1024,720)
  window.show()
  if PyQtVersion == 5 :
    sys.exit(app.exec_())
  else :
    sys.exit(app.exec())
