#!/usr/bin/env -S uv run --script
import sys

import numpy as np
import wgpu
from FloorPipeline import FloorPipeline
from ncca.ngl import Mat3, Mat4, PerspMode, PrimData, Prims, Vec3, look_at, perspective
from NumpyBufferWidget import NumpyBufferWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from TeapotPipeline import TeapotPipeline
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
        self.ratio = self.devicePixelRatio()
        self.msaa_sample_count = 4

        self.texture_size = (1024, 1024)
        self.rotation = 0.0
        self.eye = Vec3(0.0, 2.0, 4.0)
        self.view = look_at(self.eye, Vec3(0, 0, 0), Vec3(0, 1, 0))
        self.light_pos = Vec3(0.0, 2.0, 2.0)

        self.project = perspective(
            45.0, self.width() / self.height(), 0.1, 100.0, PerspMode.WebGPU
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
        # This is the texture that the multisampled texture will be resolved to
        self.colour_buffer_texture = self.device.create_texture(
            size=self.texture_size,
            sample_count=1,
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
        )
        self.colour_buffer_texture_view = self.colour_buffer_texture.create_view()

        # This is the multisampled texture that will be rendered to
        self.multisample_texture = self.device.create_texture(
            size=self.texture_size,
            sample_count=self.msaa_sample_count,
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        )
        self.multisample_texture_view = self.multisample_texture.create_view()

        # Now create a depth buffer
        depth_texture = self.device.create_texture(
            size=self.texture_size,
            format=wgpu.TextureFormat.depth24plus,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
            sample_count=self.msaa_sample_count,
        )
        self.depth_buffer_view = depth_texture.create_view()

        # Calculate aligned buffer size for texture copy
        buffer_size = self._calculate_aligned_buffer_size()
        self.readback_buffer = self.device.create_buffer(
            size=buffer_size,
            usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ,
        )

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
        width = self.ratio * self.width()
        height = self.ratio * self.height()
        self.pipelines.append(
            TeapotPipeline(
                self.device,
                self.eye,
                self.light_pos,
                self.view,
                self.project,
                width,
                height,
            )
        )
        self.pipelines.append(
            FloorPipeline(
                self.device,
                self.eye,
                self.light_pos,
                self.view,
                self.project,
                width,
                height,
            )
        )

    def paint(self) -> None:
        """
        Paint the WebGPU content.

        This method renders the WebGPU content for the scene.
        """
        self.update_uniform_buffers()
        for pipeline in self.pipelines:
            pipeline.paint(
                self.colour_buffer_texture_view,
                self.multisample_texture_view,
                self.depth_buffer_view,
            )
        self._update_colour_buffer()

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
        for pipeline in self.pipelines:
            pipeline.update_uniform_buffers(self.mouse_global_tx)

    def _update_colour_buffer(self, texture) -> None:
        """
        Update the color buffer with the rendered texture data.
        """
        buffer_size = (
            self.width() * self.height() * 4
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
                    "bytes_per_row": self.width()
                    * 4,  # Row stride (width * bytes per pixel)
                    "rows_per_image": self.height(),  # Number of rows in the texture
                },
                (self.width(), self.height(), 1),  # Copy size: width, height, depth
            )
            self.device.queue.submit([command_encoder.finish()])

            # Map the buffer for reading
            readback_buffer.map_sync(mode=wgpu.MapMode.READ)

            # Access the mapped memory
            raw_data = readback_buffer.read_mapped()
            self.frame_buffer = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (
                    self.width(),
                    self.height(),
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
        self.frame_buffer = np.zeros([self.height(), self.width(), 4], dtype=np.uint8)

    def resizeEvent(self, event) -> None:
        """
        Called whenever the window is resized.
        It's crucial to update the viewport and projection matrix here.

        Args:
            event: The resize event object.
        """
        # Update the stored width and height, considering high-DPI displays
        width = int(event.size().width() * self.ratio)
        height = int(event.size().height() * self.ratio)

        # Update texture size to match window dimensions
        self.texture_size = (width, height)

        # Update projection matrix
        self.project = perspective(
            45.0, width / height if height > 0 else 1, 0.1, 350.0, PerspMode.WebGPU
        )

        # Recreate render buffers for the new window size
        self._create_render_buffer()

        # Resize the numpy buffer to match new window dimensions
        if self.frame_buffer is not None:
            self.frame_buffer = np.zeros([height, width, 4], dtype=np.uint8)
        for pipeline in self.pipelines:
            pipeline.buffer_width = width
            pipeline.buffer_height = height

        self.update()

    def _calculate_aligned_row_size(self) -> int:
        """
        Calculate the aligned row size for texture copy operations.
        Many GPUs require row alignment to 256 or 512 bytes.
        """
        bytes_per_pixel = 4  # RGBA8 = 4 bytes per pixel
        raw_row_size = self.texture_size[0] * bytes_per_pixel

        # Align to 256 bytes (common GPU requirement)
        alignment = 256
        aligned_row_size = ((raw_row_size + alignment - 1) // alignment) * alignment

        return aligned_row_size

    def _calculate_aligned_buffer_size(self) -> int:
        """
        Calculate the aligned buffer size needed for texture copy operations.
        Many GPUs require row alignment to 256 or 512 bytes.
        """
        aligned_row_size = self._calculate_aligned_row_size()
        return aligned_row_size * self.texture_size[1]

    def _update_colour_buffer(self) -> None:
        """
        Update the colour buffer with the rendered texture data.
        """
        # Use the aligned row size calculation
        bytes_per_row = self._calculate_aligned_row_size()

        try:
            command_encoder = self.device.create_command_encoder()
            command_encoder.copy_texture_to_buffer(
                {"texture": self.colour_buffer_texture},
                {
                    "buffer": self.readback_buffer,
                    "bytes_per_row": bytes_per_row,  # Aligned row stride
                    "rows_per_image": self.texture_size[
                        1
                    ],  # Number of rows in the texture
                },
                (
                    self.texture_size[0],
                    self.texture_size[1],
                    1,
                ),  # Copy size: width, height, depth
            )
            self.device.queue.submit([command_encoder.finish()])

            # Map the buffer for reading
            self.readback_buffer.map_sync(mode=wgpu.MapMode.READ)

            # Access the mapped memory
            raw_data = self.readback_buffer.read_mapped()
            width, height = self.texture_size

            # Create a strided view of the raw data and then copy it to a contiguous array.
            # This is necessary because the raw data from the buffer includes padding bytes
            # to meet row alignment requirements, so we can't just reshape it.
            strided_view = np.lib.stride_tricks.as_strided(
                np.frombuffer(raw_data, dtype=np.uint8),
                shape=(height, width, 4),
                strides=(bytes_per_row, 4, 1),
            )
            self.frame_buffer = np.copy(strided_view)

            # Unmap the buffer when done
            self.readback_buffer.unmap()
        except Exception as e:
            print(f"Failed to update colour buffer: {e}")
            # Fallback: create a simple gray buffer if texture copy fails
            if self.frame_buffer is not None:
                self.frame_buffer.fill(128)

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
    win.resize(1024, 720)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
