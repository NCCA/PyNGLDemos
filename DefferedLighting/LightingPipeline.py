import numpy as np
import wgpu


class LightingPipeline:
    def __init__(self, device, g_buffer_textures, view_buffer, width, height):
        self.device = device
        self.pipeline = None
        self.bind_group = None
        self.g_buffer_textures = g_buffer_textures
        self.view_buffer = view_buffer
        self.width = width
        self.height = height
        self._create_light_buffer()
        self._create_render_pipeline()

    def _create_light_buffer(self):
        # Create a buffer for the lights
        light_dtype = np.dtype(
            {
                "names": ["position", "color"],
                "formats": [(np.float32, 3), (np.float32, 3)],
                "offsets": [0, 16],
                "itemsize": 32,
            }
        )
        # two lights
        self.lights = np.zeros(20, dtype=light_dtype)
        self.lights[0]["position"] = (2.0, 2.0, 2.0)
        self.lights[0]["color"] = (400.0, 400.0, 400.0)
        self.lights[1]["position"] = (-2.0, 2.0, -2.0)
        self.lights[1]["color"] = (400.0, 0.0, 0.0)

        light_uniform_dtype = np.dtype(
            {
                "names": ["lights", "num_lights"],
                "formats": [(self.lights.dtype, 20), np.uint32],
                "itemsize": 656,
            }
        )

        self.light_uniforms = np.zeros((), dtype=light_uniform_dtype)
        self.light_uniforms["lights"] = self.lights
        self.light_uniforms["num_lights"] = 2

        self.light_buffer = self.device.create_buffer_with_data(
            data=self.light_uniforms.tobytes(),
            usage=wgpu.BufferUsage.UNIFORM,
            label="light_uniform_buffer",
        )

    def _create_render_pipeline(self):
        with open("lighting.wgsl", "r") as f:
            shader_code = f.read()
        shader_module = self.device.create_shader_module(code=shader_code)

        self.pipeline = self.device.create_render_pipeline(
            label="lighting_pipeline",
            layout="auto",
            vertex={
                "module": shader_module,
                "entry_point": "vertex_main",
                "buffers": [],
            },
            fragment={
                "module": shader_module,
                "entry_point": "fragment_main",
                "targets": [{"format": wgpu.TextureFormat.rgba8unorm}],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list},
        )

        self.bind_group = self.device.create_bind_group(
            layout=self.pipeline.get_bind_group_layout(0),
            entries=[
                {
                    "binding": 0,
                    "resource": self.g_buffer_textures["position"].create_view(),
                },
                {
                    "binding": 1,
                    "resource": self.g_buffer_textures["normal"].create_view(),
                },
                {
                    "binding": 2,
                    "resource": self.g_buffer_textures["albedo"].create_view(),
                },
                {
                    "binding": 3,
                    "resource": {
                        "buffer": self.light_buffer,
                        "offset": 0,
                        "size": self.light_buffer.size,
                    },
                },
                {
                    "binding": 4,
                    "resource": {
                        "buffer": self.view_buffer,
                        "offset": 0,
                        "size": self.view_buffer.size,
                    },
                },
            ],
        )

    def paint(self, texture_view):
        command_encoder = self.device.create_command_encoder()
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[
                {
                    "view": texture_view,
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                    "clear_value": (0.0, 0.0, 0.0, 1.0),
                }
            ]
        )
        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.draw(6)
        render_pass.end()
        self.device.queue.submit([command_encoder.finish()])
