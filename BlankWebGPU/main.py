#!/usr/bin/env -S uv run --active --script
import sys

import wgpu
import wgpu.utils
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from WebGPUWidget import WebGPUWidget
from wgpu.utils import get_default_device


class WebGPUScene(WebGPUWidget):
    """
    A concrete implementation of WebGPUWidget for a WebGPU scene.

    This class implements the abstract methods to provide functionality for initializing,
    painting, and resizing the WebGPU context.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BlankWebGPU")
        self.msaa_sample_count = 4
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
        except Exception as e:
            print(f"Failed to initialize WebGPU: {e}")

    def resizeWebGPU(self, width, height) -> None:
        """
        Called whenever the window is resized.
        It's crucial to update the viewport and projection matrix here.

        Args:
            width: The new width of the window.
            height: The new height of the window.

        """

        self.update()

    def paint(self) -> None:
        """
        Paint the WebGPU content.

        This method renders the WebGPU content for the scene.
        """
        try:
            command_encoder = self.device.create_command_encoder()
            render_pass = command_encoder.begin_render_pass(
                color_attachments=[
                    {
                        "view": self.multisample_texture_view,
                        "resolve_target": self.colour_buffer_texture_view,
                        "load_op": wgpu.LoadOp.clear,
                        "store_op": wgpu.StoreOp.store,
                        "clear_value": (0.3, 0.3, 0.3, 1.0),
                    }
                ]
            )
            render_pass.end()
            self.device.queue.submit([command_encoder.finish()])
            self._update_colour_buffer()
        except Exception as e:
            print(f"Failed to paint WebGPU content: {e}")

    def keyPressEvent(self, event) -> None:
        """
        Handles keyboard press events.

        Args:
            event: The QKeyEvent object containing information about the key press.
        """
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()  # Exit the application
        self.update()

        # Call the base class implementation for any unhandled events
        super().keyPressEvent(event)


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
