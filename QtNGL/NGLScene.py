try : # support either PyQt5 or 6
  from PyQt5.QtGui import QMainWindow,QSurfaceFormat
  from PyQt5.QtWidgets import QApplication,QOpenGLWidget,QColourDialog
  from PyQt5.QtCore import *
  from PyQt5 import uic
  PyQtVersion = 5
except ImportError:
  print('trying Qt6')
  from PyQt6.QtGui import QSurfaceFormat
  from PyQt6.QtWidgets import QApplication,QMainWindow,QColorDialog
  from PyQt6.QtOpenGLWidgets import QOpenGLWidget
  from PyQt6.QtCore import QEvent,Qt
  from PyQt6 import uic
  PyQtVersion = 6

import sys
from pyngl import *
from OpenGL.GL import *

class NGLScene(QOpenGLWidget) :

  def __init__(self, parent=None) :
    super(QOpenGLWidget, self).__init__(parent)
    self.position=Vec3(0,0,0)
    self.scale=Vec3(1,1,1)
    self.rotation=Vec3()
    self.transform=Transformation()
    self.width=int(1024)
    self.height=int(720)
    self.lightPos=Vec4()
    self.wireframe=False
    self.model='teapot'


  def initializeGL(self) :
    self.makeCurrent()
    NGLInit.initialize()
    glClearColor( 0.4, 0.4, 0.4, 1.0 ) 
    glEnable( GL_DEPTH_TEST )
    glEnable( GL_MULTISAMPLE )
    ShaderLib.loadShader('PBR','../shaders/PBRVertex.glsl','../shaders/PBRFragment.glsl',ErrorExit.OFF)
    ShaderLib.use('PBR')

    # We now create our view matrix for a static camera
    From=Vec3(0.0, 2.0, 2.0 ) 
    to=Vec3( 0.0, 0.0, 0.0 ) 
    up=Vec3( 0.0, 1.0, 0.0 ) 
    # now load to our new camera
    self.view=lookAt(From,to,up) 
    self.projection=perspective( 45.0, float( self.width  / self.height), 0.1, 200.0 )
    ShaderLib.setUniform( 'camPos', From ) 
    # now a light
    self.lightPos.set( 0.0, 2.0, 2.0 ,1.0) 
    # setup the default shader material and light properties
    # these are 'uniform' so will retain their values
    ShaderLib.setUniform('lightPosition',self.lightPos.toVec3()) 
    ShaderLib.setUniform('lightColor',400.0,400.0,400.0) 
    ShaderLib.setUniform('exposure',2.2) 
    ShaderLib.setUniform('albedo',0.950, 0.71, 0.29) 

    ShaderLib.setUniform('metallic',1.02) 
    ShaderLib.setUniform('roughness',0.38) 
    ShaderLib.setUniform('ao',0.2) 
    VAOPrimitives.createSphere('sphere',1.0,40);

   

  def loadMatricesToShader(self) :
    ShaderLib.use('PBR')
    M=self.transform.getMatrix()
    MVP=self.projection*self.view*M
    normalMatrix=M
    normalMatrix.inverse().transpose() 
    ShaderLib.setUniform('M',M)
    ShaderLib.setUniform('MVP',MVP)
    ShaderLib.setUniform('normalMatrix',normalMatrix)
  
  def paintGL(self):
    try :
      self.makeCurrent()
      glViewport( 0, 0, self.width, self.height )
      glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
      ShaderLib.use('PBR')
      self.transform.setPosition(self.position)
      self.transform.setScale(self.scale)
      self.transform.setRotation(self.rotation)
    
      if(self.wireframe == True) :
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
      else :
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)

      self.loadMatricesToShader()
      VAOPrimitives.draw(self.model)

      

    except OpenGL.error.GLError :
      print( 'error')

  def resizeGL(self, w,h) :
    self.width=int(w* self.devicePixelRatio())
    self.height=int(h* self.devicePixelRatio())
    self.projection=perspective( 45.0, float( self.width)  / self.height, 0.1, 200.0 )
 
  def toggleWireframe(self) :
    self.wireframe^=True
    self.update()
  def setModel(self,model) :
    self.model=model
    self.update()

  def setRotationX(self,v) :
    self.rotation.m_x=v
    self.update()
  def setRotationY(self,v) :
    self.rotation.m_y=v
    self.update()
  def setRotationZ(self,v) :
    self.rotation.m_z=v
    self.update()
  
  def setScale(self,v,axis) :
    if axis == 'x' :
      self.scale.m_x=v.value()
    elif axis == 'y' :
      self.scale.m_y=v.value()
    elif axis == 'z' :
      self.scale.m_z=v.value()
    self.update()
  
  def setPosition(self,v,axis) :
    if axis == 'x' :
      self.position.m_x=v.value()
    elif axis == 'y' :
      self.position.m_y=v.value()
    elif axis == 'z' :
      self.position.m_z=v.value()
    self.update()

  def setColour(self) :
    colour = QColorDialog.getColor()
    if colour.isValid() :
      ShaderLib.use('PBR')
      ShaderLib.setUniform('albedo',colour.redF(),colour.greenF(),colour.blueF())
      self.update()

