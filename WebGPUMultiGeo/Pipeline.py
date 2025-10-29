import numpy as np
import wgpu
from ncca.ngl import PrimData, Prims

_FLOAT_SIZE = np.dtype(np.float32).itemsize
_TEXTURE_FORMAT = wgpu.TextureFormat.rgba8unorm


class Pipeline:
    def __init__(self, device, eye, light_pos, view, project):
        self.device = device
        self.pipeline = None
        self.transform_buffer = None
        self.material_buffer = None
        self.light_buffer = None
        self.view_buffer = None
        self.bind_group_0 = None
        self.bind_group_1 = None
        self.vertex_uniforms = None
        self.light_uniforms = None
        self.eye = eye
        self.light_pos = light_pos
        self.view = view
        self.project = project
        self.prim_buffers = {}
        self._create_buffers()
        self._create_render_pipeline()

    def _create_buffers(self):
        teapot = PrimData.primitive(Prims.TEAPOT.value)
        self.prim_buffers[Prims.TEAPOT] = [
            self.device.create_buffer_with_data(
                data=teapot, usage=wgpu.BufferUsage.VERTEX
            ),
            teapot.size // 8,
        ]
        buddah = PrimData.primitive(Prims.BUDDHA.value)
        self.prim_buffers[Prims.BUDDHA] = [
            self.device.create_buffer_with_data(
                data=buddah, usage=wgpu.BufferUsage.VERTEX
            ),
            buddah.size // 8,
        ]

    def _create_render_pipeline(self) -> None:
        """
        Create a render pipeline.
        """
        with open("DiffuseShader.wgsl", "r") as f:
            shader_code = f.read()
            shader = self.device.create_shader_module(code=shader_code)
        label = "diffuse_triangle_pipeline"
        vertex = {
            "module": shader,
            "entry_point": "vertex_main",
            "buffers": [
                {
                    "array_stride": 8 * _FLOAT_SIZE,  # x,y,z nx,ny,nz,u,v
                    "attributes": [
                        {
                            "shader_location": 0,
                            "offset": 0 * _FLOAT_SIZE,
                            "format": "float32x3",
                        },
                        {
                            "shader_location": 1,
                            "offset": 3 * _FLOAT_SIZE,
                            "format": "float32x3",
                        },
                        {
                            "shader_location": 2,
                            "offset": 6 * _FLOAT_SIZE,
                            "format": "float32x2",
                        },
                    ],
                }
            ],
        }
        fragment = {
            "module": shader,
            "entry_point": "fragment_main",
            "targets": [{"format": _TEXTURE_FORMAT}],
        }
        # Create a uniform buffer this is the layout of each uniform
        # there will be 1 for each mesh
        self.vertex_uniform_data = np.zeros(
            (),
            dtype=[
                ("MVP", "float32", (4, 4)),
                ("model_view", "float32", (4, 4)),
                ("normal_matrix", "float32", (4, 4)),  # need 4x4 for mat3
                ("colour", "float32", (4)),
                ("padding", "float32", (12)),  # to 256 bytes
            ],
        )
        num_meshes = len(self.prim_buffers.items())
        buffer_size = num_meshes * self.vertex_uniform_data.nbytes
        self.vertex_uniform_buffer = self.device.create_buffer(
            size=buffer_size,
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
            label="vertex_uniform_data",
        )

        # Create a uniform buffer for the light. This is just a single light
        light_uniform_data = np.zeros(
            (), dtype=[("light_pos", "float32", (4)), ("light_diffuse", "float32", (4))]
        )

        self.light_uniform_buffer = self.device.create_buffer_with_data(
            data=light_uniform_data.tobytes(),
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
            label="light_uniform_data",
        )
        # bind the uniforms to the shader stages. The vertex uniform is used in both
        # the vertex and fragment shaders. The light uniform is only used in the fragment shader.
        # note the use of dynamic offsets for the vertex uniform buffer as we have an array of them
        #  We cant use get_bind_group_layout(0) as it can't determine if it dynamic or not.
        bind_group_layout_0 = self.device.create_bind_group_layout(
            label="vertex_uniform_bind_group_layout",
            entries=[
                {
                    "binding": 0,
                    "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                    "buffer": {
                        "type": wgpu.BufferBindingType.uniform,
                        "has_dynamic_offset": True,
                    },
                },
                {
                    "binding": 1,
                    "visibility": wgpu.ShaderStage.FRAGMENT,
                    "buffer": {
                        "type": wgpu.BufferBindingType.uniform,
                        "has_dynamic_offset": False,
                    },
                },
            ],
        )

        # Create the bind group
        self.bind_group_0 = self.device.create_bind_group(
            label="vertex_uniform_bind_group",
            layout=bind_group_layout_0,
            entries=[
                {
                    "binding": 0,
                    "resource": {
                        "label": "vertex_uniform_buffer",
                        "buffer": self.vertex_uniform_buffer,
                        "offset": 0,  # Initial offset
                        "size": 256,  # Size of the buffer
                    },
                },
                {"binding": 1, "resource": {"buffer": self.light_uniform_buffer}},
            ],
        )

        layout = self.device.create_pipeline_layout(
            label="diffuse_triangle_pipeline_layout",
            bind_group_layouts=[bind_group_layout_0],
        )
        # finally create the pipeline
        self.pipeline = self.device.create_render_pipeline(
            label=label,
            layout=layout,
            vertex=vertex,
            fragment=fragment,
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_list,
                "front_face": wgpu.FrontFace.ccw,
                "cull_mode": wgpu.CullMode.none,
            },
            depth_stencil={
                "format": wgpu.TextureFormat.depth24plus,
                "depth_write_enabled": True,
                "depth_compare": wgpu.CompareFunction.less,
            },
            multisample={
                "count": 1,
                "mask": 0xFFFFFFFF,
                "alpha_to_coverage_enabled": False,
            },
        )

    def update_uniform_buffers(self, index, model, colour) -> None:
        """
        update the uniform buffers.
        """
        model_view = self.view @ model
        MVP = self.project @ model_view
        normal_matrix = model_view.copy()
        normal_matrix.inverse().transpose()

        self.vertex_uniform_data["model_view"] = model_view.to_numpy()
        self.vertex_uniform_data["MVP"] = MVP.to_numpy()
        self.vertex_uniform_data["normal_matrix"] = normal_matrix.to_numpy()
        self.vertex_uniform_data["colour"] = colour
        self.device.queue.write_buffer(
            buffer=self.vertex_uniform_buffer,
            buffer_offset=self.vertex_uniform_data.nbytes * index,
            data=self.vertex_uniform_data.tobytes(),
        )

    def begin_render_pass(self, texture_view, depth_buffer_view):
        self.command_encoder = self.device.create_command_encoder()
        self.render_pass = self.command_encoder.begin_render_pass(
            color_attachments=[
                {
                    "view": texture_view,
                    "resolve_target": None,
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                    "clear_value": (0.3, 0.3, 0.3, 1.0),
                }
            ],
            depth_stencil_attachment={
                "view": depth_buffer_view,
                "depth_load_op": wgpu.LoadOp.clear,
                "depth_store_op": wgpu.StoreOp.store,
                "depth_clear_value": 1.0,
            },
        )
        self.render_pass.set_viewport(0, 0, 1024, 1024, 0, 1)
        self.render_pass.set_pipeline(self.pipeline)

    def render_mesh(self, mesh: str, transform, colour, index) -> None:
        """
        Paint the WebGPU content.

        This method renders the WebGPU content for the scene.
        """
        self.update_uniform_buffers(index, transform, colour)
        self.render_pass.set_bind_group(0, self.bind_group_0, [index * 256], 0, 999999)
        self.render_pass.set_bind_group(1, self.bind_group_0, [index * 256], 0, 999999)
        self.render_pass.set_vertex_buffer(0, self.prim_buffers[mesh][0])

        self.render_pass.draw(self.prim_buffers[mesh][1])

    def end_render_pass(self) -> None:
        self.render_pass.end()
        self.device.queue.submit([self.command_encoder.finish()])
