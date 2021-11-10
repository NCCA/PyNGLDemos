from pyngl import *
from OpenGL.GL import *
import sdl2
class NGLScene :
  def __init__(self) :
    self.mouseGlobalTX=Mat4()
    self.width=int(1024)
    self.height=int(720)
    self.spinXFace = int(0)
    self.spinYFace = int(0)
    self.rotate = False
    self.translate = False
    self.origX = int(0)
    self.origY = int(0)
    self.origXPos = int(0)
    self.origYPos = int(0)
    self.INCREMENT=0.01
    self.ZOOM=0.05
    self.modelPos=Vec3()
    self.lightPos=Vec4()
    self.transformLight=False

  def initialize(self) :
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
    VAOPrimitives.createTrianglePlane('floor',20,20,1,1,Vec3.up()) 
    ShaderLib.printRegisteredUniforms('PBR')
    ShaderLib.use(nglCheckerShader) 
    ShaderLib.setUniform('lightDiffuse',1.0,1.0,1.0,1.0) 
    ShaderLib.setUniform('checkOn',1) 
    ShaderLib.setUniform('lightPos',self.lightPos.toVec3()) 
    ShaderLib.setUniform('colour1',0.9,0.9,0.9,1.0) 
    ShaderLib.setUniform('colour2',0.6,0.6,0.6,1.0) 
    ShaderLib.setUniform('checkSize',60.0) 
    ShaderLib.printRegisteredUniforms(nglCheckerShader)
    

  def loadMatricesToShader(self) :
    ShaderLib.use('PBR')
    M=self.view*self.mouseGlobalTX
    MVP=self.projection*M
    normalMatrix=M
    normalMatrix.inverse().transpose() 
    ShaderLib.setUniform('M',M)
    ShaderLib.setUniform('MVP',MVP)
    ShaderLib.setUniform('normalMatrix',normalMatrix)
    if self.transformLight == True :
      ShaderLib.setUniform('lightPosition',(self.mouseGlobalTX*self.lightPos).toVec3())
    
  def render(self):
    try :
      glViewport( 0, 0, self.width, self.height )
      glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
      ShaderLib.use('PBR')
      rotX=Mat4() 
      rotY=Mat4() 
      rotX.rotateX( self.spinXFace ) 
      rotY.rotateY( self.spinYFace ) 
      self.mouseGlobalTX = rotY * rotX 
      self.mouseGlobalTX.m_30  = self.modelPos.m_x 
      self.mouseGlobalTX.m_31  = self.modelPos.m_y 
      self.mouseGlobalTX.m_32  = self.modelPos.m_z 
      self.loadMatricesToShader()
      VAOPrimitives.draw('teapot')
      
      ShaderLib.use(nglCheckerShader)
      tx=Mat4()
      tx.translate(0.0,-0.45,0.0)
      MVP=self.projection*self.view*self.mouseGlobalTX*tx
      normalMatrix=Mat3(self.view*self.mouseGlobalTX)
      normalMatrix.inverse().transpose()
      ShaderLib.setUniform('MVP',MVP)
      ShaderLib.setUniform('normalMatrix',normalMatrix)
      VAOPrimitives.draw('floor')

    except OpenGL.error.GLError :
      print( 'error')

  def resize(self, w,h) :
    self.width=int(w)
    self.height=int(h)
    self.projection=perspective( 45.0, float( self.width)  / self.height, 0.1, 200.0 )



  def mousePressEvent(self,event) :
    if  event.button == sdl2.SDL_BUTTON_LEFT :
      print("left")
      self.origX  = event.x
      self.origY  = event.y
      self.rotate = True

    elif  event.button == sdl2.SDL_BUTTON_RIGHT :
      self.origXPos  = event.x 
      self.origYPos  = event.y 
      self.translate = True

  def mouseReleaseEvent(self,event) :
    if  event.button == sdl2.SDL_BUTTON_LEFT  :
      self.rotate = False

    elif  event.button == sdl2.SDL_BUTTON_RIGHT :
      self.translate = False
  
  def mouseMoveEvent(self,event) :

    if self.rotate and event.button == sdl2.SDL_BUTTON_LEFT  :
      diffx = int(event.x - self.origX)
      diffy = int(event.y - self.origY)
      self.spinXFace += int( 0.5 * diffy )
      self.spinYFace += int( 0.5 * diffx )
      self.origX = event.x
      self.origY = event.y
    elif self.translate and event.button == sdl2.SDL_BUTTON_RIGHT :
      diffX   = int( event.x - self.origXPos )
      diffY   = int( event.y - self.origYPos )
      self.origXPos = event.x
      self.origYPos = event.y
      self.modelPos.m_x += self.INCREMENT * diffX 
      self.modelPos.m_y -= self.INCREMENT * diffY 

  def wheelEvent(self,event) :
    if  event.y > 0  :
      self.modelPos.m_z += self.ZOOM
    elif  event.y < 0 :
      self.modelPos.m_z -= self.ZOOM
    if event.x> 0 :
      self.modelPos.m_x-=self.ZOOM
    elif event.x<0 :
      self.modelPos.m_x+=self.ZOOM