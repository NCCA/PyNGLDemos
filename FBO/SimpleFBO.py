#!/usr/bin/env python
try : # support either PyQt5 or 6
  from PyQt5.QtGui import QOpenGLWindow,QSurfaceFormat
  from PyQt5.QtWidgets import QApplication
  from PyQt5.QtCore import *
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
    self.width=int(1024)
    self.height=int(720)
    self.setTitle('Simple FBO Demo')
    self.spinXFace = int(0)
    self.spinYFace = int(0)
    self.rotate = False
    self.translate = False
    self.origX = int(0)
    self.origY = int(0)
    self.origXPos = int(0)
    self.origYPos = int(0)
    self.INCREMENT=0.01
    self.ZOOM=0.1
    self.modelPos=Vec3()
    self.lightPos=Vec4()
    self.transformLight=False
    self.textureWidth=1024
    self.textureHeight=1024
    self.rot=0.0
    self.transform=Transformation()

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
    ShaderLib.loadShader('TextureShader','../shaders/TextureVertex.glsl','../shaders/TextureFragment.glsl',ErrorExit.OFF)
    self.createTextureObject()
    self.createFramebufferObject()
    VAOPrimitives.createTrianglePlane('plane',2,2,20,20,Vec3(0,1,0))
    VAOPrimitives.createSphere('sphere',0.4,80);
    self.startTimer(1)

   

  def loadMatricesToShader(self) :
    ShaderLib.use('PBR')
    M=self.transform.getMatrix()
    MVP=self.projection*self.view*M
    normalMatrix=M
    normalMatrix.inverse().transpose() 
    ShaderLib.setUniform('M',M)
    ShaderLib.setUniform('MVP',MVP)
    ShaderLib.setUniform('normalMatrix',normalMatrix)
    if self.transformLight == True :
      ShaderLib.setUniform('lightPosition',(self.mouseGlobalTX*self.lightPos).toVec3())
    
  def paintGL(self):
    try :
      self.makeCurrent()
      # we are now going to draw to our FBO
      # set the rendering destination to FBO
      glBindFramebuffer(GL_FRAMEBUFFER, self.fboID)
      # set the background colour (using blue to show it up)
      glClearColor(0,0.4,0.5,1)
      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
      # set our viewport to the size of the texture
      # if we want a different camera we wouldset this here
      glViewport(0, 0, self.textureWidth, self.textureHeight)
      # rotate the teapot
      self.transform.reset()
      self.transform.setRotation(self.rot,self.rot,self.rot)
      self.loadMatricesToShader()
      VAOPrimitives.draw("teapot")

      # Now draw into default framebuffer
      # first bind the normal render buffer
      glBindFramebuffer(GL_FRAMEBUFFER, self.defaultFramebufferObject())
      # now enable the texture we just rendered to
      glBindTexture(GL_TEXTURE_2D, self.textureID)
      # do any mipmap generation
      # glGenerateMipmap(GL_TEXTURE_2D);
      # set the screen for a different clear colour
      glClearColor(0.4, 0.4, 0.4, 1.0)			   # Grey Background
      # clear this screen
      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
      rotX=Mat4() 
      rotY=Mat4() 
      rotX.rotateX( self.spinXFace ) 
      rotY.rotateY( self.spinYFace ) 
      self.mouseGlobalTX = rotY * rotX 
      self.mouseGlobalTX.m_30  = self.modelPos.m_x 
      self.mouseGlobalTX.m_31  = self.modelPos.m_y 
      self.mouseGlobalTX.m_32  = self.modelPos.m_z 

      # get the new shader and set the new viewport size
      ShaderLib.use('TextureShader')
      # this takes into account retina displays etc
      glViewport(0, 0, self.width,self.height)
      self.transform.reset()
      MVP= self.projection*self.view*self.mouseGlobalTX
      ShaderLib.setUniform("MVP",MVP)
      VAOPrimitives.draw("plane")
      self.transform.setPosition(0,1,0)
      MVP= self.projection*self.view*self.mouseGlobalTX*self.transform.getMatrix()
      ShaderLib.setUniform("MVP",MVP)
      VAOPrimitives.draw("sphere")


      
      
      
      # glViewport( 0, 0, self.width, self.height )
      # glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
      # ShaderLib.use('PBR')
      # rotX=Mat4() 
      # rotY=Mat4() 
      # rotX.rotateX( self.spinXFace ) 
      # rotY.rotateY( self.spinYFace ) 
      # self.mouseGlobalTX = rotY * rotX 
      # self.mouseGlobalTX.m_30  = self.modelPos.m_x 
      # self.mouseGlobalTX.m_31  = self.modelPos.m_y 
      # self.mouseGlobalTX.m_32  = self.modelPos.m_z 
      # self.loadMatricesToShader()
      # VAOPrimitives.draw('teapot')
      
      # ShaderLib.use(nglCheckerShader)
      # tx=Mat4()
      # tx.translate(0.0,-0.45,0.0)
      # MVP=self.projection*self.view*self.mouseGlobalTX*tx
      # normalMatrix=Mat3(self.view*self.mouseGlobalTX)
      # normalMatrix.inverse().transpose()
      # ShaderLib.setUniform('MVP',MVP)
      # ShaderLib.setUniform('normalMatrix',normalMatrix)
      # VAOPrimitives.draw('floor')

    except OpenGL.error.GLError :
      print( 'error')

  def resizeGL(self, w,h) :
    self.width=int(w* self.devicePixelRatio())
    self.height=int(h* self.devicePixelRatio())
    self.projection=perspective( 45.0, float( self.width)  / self.height, 0.1, 200.0 )
 

  def createTextureObject(self) :
    # create a texture object
    self.textureID=glGenTextures(1)
    # bind it to make it active
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, self.textureID)
    # set params
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    #//glGenerateMipmapEXT(GL_TEXTURE_2D);  // set the data size but just set the buffer to 0 as we will fill it with the FBO
           
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self.textureWidth, self.textureHeight, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
    # now turn the texture off for now
    glBindTexture(GL_TEXTURE_2D, 0)

  def createFramebufferObject(self) :
    # create a framebuffer object this is deleted in the dtor
    self.fboID=glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, self.fboID)
    # create a renderbuffer object to store depth info
    rboID=glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, rboID)

    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.textureWidth, self.textureHeight)
    # bind
    glBindRenderbuffer(GL_RENDERBUFFER, 0)

    # attatch the texture we created earlier to the FBO
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.textureID, 0)

    # now attach a renderbuffer to depth attachment point
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rboID)
    # now got back to the default render context
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    # were finished as we have an attached RB so delete it
    glDeleteRenderbuffers(1,rboID)

  def timerEvent(self,event) :
    self.rot=self.rot+0.1
    self.update()


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
        self.spinXFace +=  0.5 * diffy 
        self.spinYFace +=  0.5 * diffx 
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
      if  numPixels.y() > 0  :
        self.modelPos.m_x += self.ZOOM

      elif  numPixels.y() < 0 :
        self.modelPos.m_x -= self.ZOOM


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
    # todo try and capture Mac gestures
    def nativeEvent(self,event,message) :
      retval, result = super(QOpenGLWindow, self).nativeEvent(event, message)
      return retval,result


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
