from abc import ABCMeta, abstractmethod
from typing import List, Tuple

import numpy as np
from PySide6.QtCore import QObject, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QWidget


class QWidgetABCMeta(ABCMeta, type(QWidget)):
    """
    A metaclass that combines the functionality of ABCMeta and QWidget's metaclass.

    This allows the creation of abstract base classes that are also QWidgets.
    """

    pass


class NumpyBufferWidget(QWidget, metaclass=QWidgetABCMeta):
    """
    An abstract base class for NumpyBufferWidget widgets.

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
        self.buffer = None
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update)

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

        if self.buffer is not None:
            self._present_image(painter, self.buffer)
        for x, y, text, size, font, colour in self.text_buffer:
            painter.setPen(colour)
            painter.setFont(QFont("Arial", size))
            painter.drawText(x, y, text)
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

        Args:
            x (int): The x-coordinate of the text.
            y (int): The y-coordinate of the text.
            text (str): The text to render.
            size (int, optional): The font size of the text. Defaults to 10.
            font (str, optional): The font family of the text. Defaults to "Arial".
            colour (QColor, optional): The colour of the text. Defaults to Qt.black.
        """
        self.text_buffer.append((x, y, text, size, font, colour))

    def resizeEvent(self, event) -> None:
        """
        Handle the resize event to adjust the WebGPU context.

        Args:
            event (QResizeEvent): The resize event.
        """
        return super().resizeEvent(event)

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
            width * 4,
            QImage.Format.Format_RGBX8888,
        )

        rect1 = QRect(0, 0, width, height)
        rect2 = self.rect()
        painter.drawImage(rect2, image, rect1)
