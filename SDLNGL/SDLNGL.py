#!/usr/bin/env python

import sdl2
from NGLScene import NGLScene
from OpenGL.GL import *
import sys

class SDLWindow :
  def __init__(self) :
    self.ActiveButton=None
    self.scene=NGLScene()

    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(sdl2.SDL_GetError())
        return -1
    self.window = sdl2.SDL_CreateWindow(b"OpenGL demo",
                                   sdl2.SDL_WINDOWPOS_UNDEFINED,
                                   sdl2.SDL_WINDOWPOS_UNDEFINED, 1024, 720,
                                   sdl2.SDL_WINDOW_OPENGL)
    if not self.window:
        print(sdl2.SDL_GetError())
        return -1
    # Force OpenGL 4.1 'core' context.
    sdl2.video.SDL_GL_SetAttribute(sdl2.video.SDL_GL_CONTEXT_MAJOR_VERSION, 4)
    sdl2.video.SDL_GL_SetAttribute(sdl2.video.SDL_GL_CONTEXT_MINOR_VERSION, 1)
    sdl2.video.SDL_GL_SetAttribute(sdl2.video.SDL_GL_CONTEXT_PROFILE_MASK,sdl2.video.SDL_GL_CONTEXT_PROFILE_CORE)
    self.context = sdl2.SDL_GL_CreateContext(self.window)

    width=1024
    height=720
    self.scene.resize(width,height)
    self.scene.initialize()
  def render(self) :
    self.scene.render()
    sdl2.SDL_GL_SwapWindow(self.window)
  def cleanup(self) :
    sdl2.SDL_GL_DeleteContext(self.context)
    sdl2.SDL_DestroyWindow(self.window)
    sdl2.SDL_Quit()
    sys.exit(0)
  def mousePressEvent(self,event) :
    self.scene.mousePressEvent(event.button)
  def mouseReleaseEvent(self,event) :
    self.scene.mouseReleaseEvent(event.button)
  def mouseMoveEvent(self,event) :
    self.scene.mouseMoveEvent(event.button)
  def mouseWheelEvent(self,event) :
    self.scene.wheelEvent(event.wheel)
   

def main() :
  window=SDLWindow() 
  event = sdl2.SDL_Event()
  running = True
  while running:
    while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
      if event.type == sdl2.SDL_QUIT:
        running = False
      # on key up
      sym = event.key.keysym.sym
      if event.type == sdl2.SDL_KEYUP:
        print("keyup")
      # on_key_press
      elif event.type == sdl2.SDL_KEYDOWN:
        if sym == sdl2.SDLK_ESCAPE :
          running = False
      if event.type == sdl2.SDL_MOUSEBUTTONDOWN :
        window.mousePressEvent(event)
      if event.type == sdl2.SDL_MOUSEBUTTONUP :
        window.mouseReleaseEvent(event)
      if event.type == sdl2.SDL_MOUSEMOTION :
        window.mouseMoveEvent(event)
      if event.type == sdl2.SDL_MOUSEWHEEL :
        window.mouseWheelEvent(event)


      window.render()
  window.cleanup()

# case SDL_MOUSEMOTION : ngl.mouseMoveEvent(event.motion); break;
# case SDL_MOUSEBUTTONDOWN : ngl.mousePressEvent(event.button); break;
# case SDL_MOUSEBUTTONUP : ngl.mouseReleaseEvent(event.button); break;
# case SDL_MOUSEWHEEL : ngl.wheelEvent(event.wheel); break;


if __name__ == "__main__":
    main()