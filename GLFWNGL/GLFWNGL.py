#!/usr/bin/env python

import glfw
from NGLScene import NGLScene
from OpenGL.GL import *
import sys



class GLFWWindow :
  def __init__(self) :
    self.ActiveButton=None
    self.scene=NGLScene()
    # Initialize the library
    if not glfw.init():
      return
    # set OpenGL version and profile
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,1)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    # Create a windowed mode window and its OpenGL context
    self.window = glfw.create_window(1024, 720, "GLFW NGL", None, None)
    if not self.window:
      glfw.terminate()
      return
    # register our callbacks
    glfw.set_key_callback(self.window,self.keyboard_callback)
    glfw.set_mouse_button_callback(self.window,self.mouse_button_callback)
    glfw.set_cursor_pos_callback(self.window,self.cursor_pos_callback)
    glfw.set_scroll_callback(self.window,self.scroll_callback)

    # Make the window's context current
    glfw.make_context_current(self.window)
    width,height=glfw.get_framebuffer_size(self.window)
    self.scene.resize(width,height)
    self.scene.initialize()


  def keyboard_callback(self,window, key, scancode, action, mods) :
    if  key == glfw.KEY_ESCAPE and action == glfw.PRESS :
      # flag to set the window to close
      glfw.set_window_should_close(window,True)
    elif  key == glfw.KEY_W and action == glfw.PRESS :
      glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    elif  key == glfw.KEY_S and action == glfw.PRESS :
      glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)

  def mouse_button_callback(self,window,button,action,mods) :
    x,y=glfw.get_cursor_pos(window)
    if action == glfw.PRESS :
      self.ActiveButton=button
      self.scene.mousePressEvent(button,x,y)
    elif action == glfw.RELEASE :
      self.ActiveButton=button
      self.scene.mouseReleaseEvent(button)

  def cursor_pos_callback(self, window, x,y) :
    x,y=glfw.get_cursor_pos(window)
    self.scene.mouseMoveEvent(self.ActiveButton,x,y)

  def scroll_callback(self, window, x,y) :
    self.scene.wheelEvent(x,y)


  def should_close(self) :
    return glfw.window_should_close(self.window)
  def render(self) :
    self.scene.render()
    # Swap front and back buffers
    glfw.swap_buffers(self.window)

   

def main() :
  window=GLFWWindow() 
  # Loop until the user closes the window
  while not window.should_close()  :
    # Render here, e.g. using pyOpenGL
    window.render()
    # Poll for and process events
    glfw.poll_events()

  glfw.terminate()

if __name__ == "__main__":
    main()