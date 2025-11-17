from abc import ABCMeta, abstractmethod
from typing import List, Tuple

import numpy as np
import wgpu
from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QWidget


class QWidgetABCMeta(ABCMeta, type(QWidget)):
    """
    A metaclass that combines the functionality of ABCMeta and QWidget's metaclass.

    This allows the creation of abstract base classes that are also QWidgets.
    """

    pass


class WebGPUWidget(QWidget, metaclass=QWidgetABCMeta):
    """
    An abstract base class for WebGPUWidget widgets.

    This class allows us to generate a simple numpy buffer and render it to the screen.
    Attributes:
        initialized (bool): A flag indicating whether the widget has been initialized, default is False and will allow initializeWebGPU to be called once.
    """

    def __init__(self) -> None:
        """
        Initialize the class.

        This constructor initializes the QWidget and sets the initialized flag to False.
        """
        super().__init__()
        self.initialized = False

        self.text_buffer: List[Tuple[int, int, str, int, str, QColor]] = []
        self.frame_buffer = None
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update)
        self.ratio = self.devicePixelRatio()
        self.texture_size = (
            int(self.width() * self.ratio),
            int(self.height() * self.ratio),
        )

    def start_update_timer(self, interval_ms: int) -> None:
        """
        Starts the update timer with the given interval.

        Args:
            interval_ms (int): The interval in milliseconds.
        """
        self._update_timer.start(interval_ms)

    def stop_update_timer(self) -> None:
        """Stops the update timer."""
        self._update_timer.stop()

    @abstractmethod
    def initialize_buffer(self) -> None:
        """
        Initialize the WebGPU context.

        This method must be implemented in subclasses to set up the WebGPU context. Will be called once.
        """
        pass

    @abstractmethod
    def resizeWebGPU(self, w, h) -> None:
        """
        Initialize the WebGPU context.
        """
        pass

    def resizeEvent(self, event) -> None:
        """
        Called whenever the window is resized.

        Args:
            event: The resize event object.
        """
        # Update the stored width and height, considering high-DPI displays
        width = int(event.size().width() * self.ratio)
        height = int(event.size().height() * self.ratio)
        self.texture_size = (width, height)

        self.resizeWebGPU(width, height)

        # Recreate render buffers for the new window size
        self._create_render_buffer()

        # Resize the numpy buffer to match new window dimensions
        if self.frame_buffer is not None:
            self.frame_buffer = np.zeros([height, width, 4], dtype=np.uint8)

        return super().resizeEvent(event)

    @abstractmethod
    def paint(self) -> None:
        """
        Paint the WebGPU content.

        This method must be implemented in subclasses to render the WebGPU content. This will be called on every paint event
        and is where all the main rendering code should be placed.
        """
        pass

    def paintEvent(self, event) -> None:
        """
        Handle the paint event to render the WebGPU content.

        Args:
            event (QPaintEvent): The paint event.
        """
        if not self.initialized:
            self.initialize_buffer()
            self.initialized = True
        self.paint()
        painter = QPainter(self)

        if self.frame_buffer is not None:
            self._present_image(painter, self.frame_buffer)
        # Define a base height for font scaling 600 is a sensible default for most desktop environments
        base_height = 600.0
        scale_factor = self.height() / base_height

        for x, y, text, size, font, colour in self.text_buffer:
            scaled_size = int(size * scale_factor)
            painter.setPen(colour)
            painter.setFont(QFont(font, scaled_size))
            draw_y = y
            if y < 0:
                draw_y = self.height() + y
            painter.drawText(x, draw_y, text)
        self.text_buffer.clear()

        return super().paintEvent(event)

    def render_text(
        self,
        x: int,
        y: int,
        text: str,
        size: int = 10,
        font: str = "Arial",
        colour: QColor = Qt.black,
    ) -> None:
        """
        Add text to the buffer to be rendered on the canvas.

        The size of the text will be scaled based on the window's height.

        Args:
            x (int): The x-coordinate of the text.
            y (int): The y-coordinate of the text. A negative value will position the text relative to the bottom of the window.
            text (str): The text to render.
            size (int, optional): The base font size of the text. This will be scaled. Defaults to 10.
            font (str, optional): The font family of the text. Defaults to "Arial".
            colour (QColor, optional): The colour of the text. Defaults to Qt.black.
        """
        self.text_buffer.append((x, y, text, size, font, colour))

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

    def _present_image(self, painter, image_data: np.ndarray) -> None:
        """
        Present the image data on the canvas.

        Args:
            image_data (np.ndarray): The image data to render.
        """
        height, width, _ = image_data.shape
        image = QImage(
            image_data.data,
            width,
            height,
            image_data.strides[0],
            QImage.Format.Format_RGBA8888,
        )

        rect1 = QRect(0, 0, width, height)
        rect2 = self.rect()
        painter.drawImage(rect2, image, rect1)
