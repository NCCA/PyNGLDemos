# Font Rendering

This demo shows the PyNGL font rendering capabilities.  It shows the principles of loading true type fonts, then rendering text per frame.

## Using PyNGL.Text

We only need to load the fonts once, we typically do this in the ```initializeGL``` function as we need an OpenGL context to create the texture atlas.

```python
Text.add_font("70s", "70SdiscopersonaluseBold-w14z2.otf", FONT_SIZE)
Text.add_font("Painter", "Painter-LxXg.ttf", FONT_SIZE)
Text.add_font("Cookie", "Cookiemonster-gv11.ttf", FONT_SIZE)
Text.add_font("Arial", "Arial.ttf", 30)
```

To set the screen resolution, we can use the ```set_screen_resolution``` function.

```python
def resizeGL(self, w: int, h: int) -> None:
        Text.set_screen_size(self.window_width, self.window_height)
```


To render text we can use the ```render_text``` function.

```python
Text.render_text("Arial", 10, 440, "To Render we call")
```

With and optional colour parameter (default is white)
