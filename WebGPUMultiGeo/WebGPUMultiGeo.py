#!/usr/bin/env -S uv run --script
import sys

import numpy as np
import wgpu
from ncca.ngl import Mat4, PrimData, Prims, Transform, Vec3, Vec4, look_at, perspective
from NumpyBufferWidget import NumpyBufferWidget
from Pipeline import Pipeline
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from wgpu.utils import get_default_device


class WebGPUScene(NumpyBufferWidget):
    """
    A concrete implementation of NumpyBufferWidget for a WebGPU scene.

    This class implements the abstract methods to provide functionality for initializing,
    painting, and resizing the WebGPU context.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple WebGPU ?")
        self.device = None
        self.mouse_global_tx: Mat4 = Mat4()
        self.model_position: Vec3 = Vec3()  # Position of the model in world space
        # --- Mouse Control Attributes for Camera Manipulation ---
        self.rotate: bool = False  # Flag to check if the scene is being rotated
        self.translate: bool = (
            False  # Flag to check if the scene is being translated (panned)
        )
        self.spin_x_face: int = 0  # Accumulated rotation around the X-axis
        self.spin_y_face: int = 0  # Accumulated rotation around the Y-axis
        self.original_x_rotation: int = (
            0  # Initial X position of the mouse when a rotation starts
        )
        self.original_y_rotation: int = (
            0  # Initial Y position of the mouse when a rotation starts
        )
        self.original_x_pos: int = (
            0  # Initial X position of the mouse when a translation starts
        )
        self.original_y_pos: int = (
            0  # Initial Y position of the mouse when a translation starts
        )
        self.INCREMENT: float = 0.01  # Sensitivity for translation
        self.ZOOM: float = 0.1  # Sensitivity for zooming

        self.pipelines = []
        self.vertex_buffer = None
        self.width = 1024
        self.height = 1024
        self.texture_size = (1024, 1024)
        self.rotation = 0.0
        self.eye = Vec3(0.0, 2.0, 4.0)
        self.view = look_at(self.eye, Vec3(0, 0, 0), Vec3(0, 1, 0))
        self.light_pos = Vec4(0.0, 2.0, 2.0, 1.0)
        gl_to_web = Mat4.from_list(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.5, 0.5],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )

        self.project = gl_to_web @ perspective(
            45.0, self.width / self.height, 0.1, 100.0
        )
        self._initialize_web_gpu()
        self.update()

    def _initialize_web_gpu(self) -> None:
        """
        Initialize the WebGPU context.

        This method sets up the WebGPU context for the scene.
        """
        print("initializeWebGPU")
        try:
            self.device = get_default_device()
            self._create_render_buffer()
            self._init_buffers()
            self._create_render_pipeline()
            self.startTimer(16)
        except Exception as e:
            print(f"Failed to initialize WebGPU: {e}")
            exit(1)

    def _create_render_buffer(self):
        colour_buffer_texture = self.device.create_texture(
            size=(self.width, self.height),
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
        )
        self.colour_buffer_texture = colour_buffer_texture
        self.texture_view = self.colour_buffer_texture.create_view()
        # Now create a depth buffer
        depth_texture = self.device.create_texture(
            size=(self.width, self.height),  # width, height, depth
            format=wgpu.TextureFormat.depth24plus,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        )
        self.depth_buffer_view = depth_texture.create_view()

    def _init_buffers(self):
        teapot = PrimData.primitive(Prims.TEAPOT.value)
        self.teapot_size = teapot.size // 8
        self.vertex_buffer = self.device.create_buffer_with_data(
            data=teapot, usage=wgpu.BufferUsage.VERTEX
        )

    def _create_render_pipeline(self) -> None:
        """
        Create a render pipeline.
        """
        self.pipeline = Pipeline(
            self.device, self.eye, self.light_pos, self.view, self.project
        )

    def paint(self) -> None:
        """
        Paint the WebGPU content.

        This method renders the WebGPU content for the scene.
        """
        self.update_uniform_buffers()

        self.pipeline.begin_render_pass(self.texture_view, self.depth_buffer_view)

        tx = Transform()
        tx.set_scale(0.1, 0.1, 0.1)
        tx.set_position(-1.0, 0.0, 0.0)
        self.pipeline.render_mesh(
            Prims.BUDDHA, self.mouse_global_tx @ tx.get_matrix(), 0
        )
        tx.reset()
        self.pipeline.render_mesh(
            Prims.TEAPOT, self.mouse_global_tx @ tx.get_matrix(), 1
        )
        self.pipeline.end_render_pass()
        self._update_colour_buffer(self.colour_buffer_texture)

    def update_uniform_buffers(self) -> None:
        """
        update the uniform buffers.
        """
        # Apply rotation based on user input
        rot_x = Mat4().rotate_x(self.spin_x_face)
        rot_y = Mat4().rotate_y(self.spin_y_face)
        self.mouse_global_tx = rot_y @ rot_x
        # Update model position
        self.mouse_global_tx[3][0] = self.model_position.x
        self.mouse_global_tx[3][1] = self.model_position.y
        self.mouse_global_tx[3][2] = self.model_position.z

    def _update_colour_buffer(self, texture) -> None:
        """
        Update the color buffer with the rendered texture data.
        """
        buffer_size = (
            self.width * self.height * 4
        )  # Width * Height * Bytes per pixel (RGBA8 is 4 bytes per pixel)
        try:
            readback_buffer = self.device.create_buffer(
                size=buffer_size,
                usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ,
            )
            command_encoder = self.device.create_command_encoder()
            command_encoder.copy_texture_to_buffer(
                {"texture": texture},
                {
                    "buffer": readback_buffer,
                    "bytes_per_row": self.width
                    * 4,  # Row stride (width * bytes per pixel)
                    "rows_per_image": self.height,  # Number of rows in the texture
                },
                (self.width, self.height, 1),  # Copy size: width, height, depth
            )
            self.device.queue.submit([command_encoder.finish()])

            # Map the buffer for reading
            readback_buffer.map_sync(mode=wgpu.MapMode.READ)

            # Access the mapped memory
            raw_data = readback_buffer.read_mapped()
            self.buffer = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (
                    self.width,
                    self.height,
                    4,
                )
            )  # Height, Width, Channels

            # Unmap the buffer when done
            readback_buffer.unmap()
        except Exception as e:
            print(f"Failed to update color buffer: {e}")

    def initialize_buffer(self) -> None:
        """
        Initialize the numpy buffer for rendering .

        """
        print("initialize numpy buffer")
        self.buffer = np.zeros([self.height, self.width, 4], dtype=np.uint8)

    def keyPressEvent(self, event) -> None:
        """
        Handles keyboard press events.

        Args:
            event: The QKeyEvent object containing information about the key press.
        """
        key = event.key()

        if key == Qt.Key_Escape:
            self.close()  # Exit the application
        elif key == Qt.Key_Space:
            # Reset camera rotation and position
            self.spin_x_face = 0
            self.spin_y_face = 0
            self.model_position.set(0, 0, 0)

        self.update()
        # Call the base class implementation for any unhandled events
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """
        Handles mouse movement events for camera control.

        Args:
            event: The QMouseEvent object containing the new mouse position.
        """
        # Rotate the scene if the left mouse button is pressed
        if self.rotate and event.buttons() == Qt.LeftButton:
            position = event.position()
            diff_x = position.x() - self.original_x_rotation
            diff_y = position.y() - self.original_y_rotation
            self.spin_x_face += int(0.5 * diff_y)
            self.spin_y_face += int(0.5 * diff_x)
            self.original_x_rotation = position.x()
            self.original_y_rotation = position.y()
            self.update()
        # Translate (pan) the scene if the right mouse button is pressed
        elif self.translate and event.buttons() == Qt.RightButton:
            position = event.position()
            diff_x = int(position.x() - self.original_x_pos)
            diff_y = int(position.y() - self.original_y_pos)
            self.original_x_pos = position.x()
            self.original_y_pos = position.y()
            self.model_position.x += self.INCREMENT * diff_x
            self.model_position.y -= self.INCREMENT * diff_y
            self.update()

    def mousePressEvent(self, event) -> None:
        """
        Handles mouse button press events to initiate rotation or translation.

        Args:
            event: The QMouseEvent object.
        """
        position = event.position()
        # Left button initiates rotation
        if event.button() == Qt.LeftButton:
            self.original_x_rotation = position.x()
            self.original_y_rotation = position.y()
            self.rotate = True
        # Right button initiates translation
        elif event.button() == Qt.RightButton:
            self.original_x_pos = position.x()
            self.original_y_pos = position.y()
            self.translate = True

    def mouseReleaseEvent(self, event) -> None:
        """
        Handles mouse button release events to stop rotation or translation.

        Args:
            event: The QMouseEvent object.
        """
        # Stop rotating when the left button is released
        if event.button() == Qt.LeftButton:
            self.rotate = False
        # Stop translating when the right button is released
        elif event.button() == Qt.RightButton:
            self.translate = False

    def wheelEvent(self, event) -> None:
        """
        Handles mouse wheel events for zooming.

        Args:
            event: The QWheelEvent object.
        """
        num_pixels = event.angleDelta()
        # Zoom in or out by adjusting the Z position of the model
        if num_pixels.x() > 0:
            self.model_position.z += self.ZOOM
        elif num_pixels.x() < 0:
            self.model_position.z -= self.ZOOM
        self.update()


def main():
    """
    Main function to run the application.
    Parses command line arguments and initializes the WebGPUScene.
    """
    app = QApplication(sys.argv)
    win = WebGPUScene()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
