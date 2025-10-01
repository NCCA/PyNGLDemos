import random

import numpy as np
import OpenGL.GL as gl
from ncca.ngl import Vec3, Vec3Array


class Terrain:
    def __init__(self, width: int, height: int, depth: int, num_textures: int):
        self.voxel_positions = Vec3Array(width * height * depth)
        self.is_active = np.zeros(width * height * depth, dtype=bool)
        self.texture_index = np.zeros(width * height * depth, dtype=np.uint32)
        self.width = width
        self.height = height
        self.depth = depth
        self.num_textures = num_textures
        self.buffer_ids = []
        self.texture_ids = []
        self._gen_voxels()

    def _gen_voxels(self):
        def rand_tex():
            return random.randint(0, self.num_textures)

        start_x = -self.width // 2
        start_y = -self.height // 2
        start_z = -self.depth // 2
        step = 1
        x_pos = start_x
        y_pos = start_y
        z_pos = start_z
        for x in range(self.width):
            for y in range(self.height):
                for z in range(self.depth):
                    active = rand_tex() > self.num_textures // 2
                    self._set_voxel(
                        x, y, z, Vec3(x_pos, y_pos, z_pos), rand_tex(), active
                    )

                    z_pos += step
                z_pos = start_z
                x_pos += step
            x_pos = start_x
            y_pos += step

    def gen_texture_buffer(self) -> None:
        # Generate IDs for 3 buffers and 3 textures
        self.buffer_ids = gl.glGenBuffers(3)
        self.texture_ids = gl.glGenTextures(3)

        # 1. Voxel positions buffer and texture
        voxel_data = self.voxel_positions.to_numpy()
        gl.glBindBuffer(gl.GL_TEXTURE_BUFFER, self.buffer_ids[0])
        gl.glBufferData(
            gl.GL_TEXTURE_BUFFER, voxel_data.nbytes, voxel_data, gl.GL_STATIC_DRAW
        )
        gl.glBindTexture(gl.GL_TEXTURE_BUFFER, self.texture_ids[0])
        gl.glTexBuffer(gl.GL_TEXTURE_BUFFER, gl.GL_RGB32F, self.buffer_ids[0])

        # 2. Texture index buffer and texture
        gl.glBindBuffer(gl.GL_TEXTURE_BUFFER, self.buffer_ids[1])
        gl.glBufferData(
            gl.GL_TEXTURE_BUFFER,
            self.texture_index.nbytes,
            self.texture_index,
            gl.GL_STATIC_DRAW,
        )
        gl.glBindTexture(gl.GL_TEXTURE_BUFFER, self.texture_ids[1])
        gl.glTexBuffer(gl.GL_TEXTURE_BUFFER, gl.GL_R32UI, self.buffer_ids[1])

        # 3. is_active (visibility) buffer and texture
        is_active_int = self.is_active.astype(np.uint32)
        gl.glBindBuffer(gl.GL_TEXTURE_BUFFER, self.buffer_ids[2])
        gl.glBufferData(
            gl.GL_TEXTURE_BUFFER, is_active_int.nbytes, is_active_int, gl.GL_STATIC_DRAW
        )
        gl.glBindTexture(gl.GL_TEXTURE_BUFFER, self.texture_ids[2])
        gl.glTexBuffer(gl.GL_TEXTURE_BUFFER, gl.GL_R32UI, self.buffer_ids[2])

    def activate_texture_buffer(self, pos_unit, index_unit, active_unit) -> None:
        gl.glActiveTexture(pos_unit)
        gl.glBindTexture(gl.GL_TEXTURE_BUFFER, self.texture_ids[0])

        gl.glActiveTexture(index_unit)
        gl.glBindTexture(gl.GL_TEXTURE_BUFFER, self.texture_ids[1])

        gl.glActiveTexture(active_unit)
        gl.glBindTexture(gl.GL_TEXTURE_BUFFER, self.texture_ids[2])

    def remove_index(self, index: int) -> None:
        if index > len(self.texture_index):
            return

        self.is_active[index] = False
        gl.glBindBuffer(gl.GL_TEXTURE_BUFFER, self.texture_buffer[2])
        # OpenGL doesn't have a boolean buffer type, so we convert the numpy bool array to uint32
        is_active_int = self.is_active.astype(np.uint32)
        gl.glBufferData(
            gl.GL_TEXTURE_BUFFER, is_active_int.nbytes, is_active_int, gl.GL_STATIC_DRAW
        )

    def change_texture_id(self, index: int, value: int):
        if index > len(self.texture_index):
            return

        self.texture_index[index] += value
        self.texture_index[index] = np.clip(
            self.texture_index[index], int(0), int(self.num_textures)
        )
        gl.glBindBuffer(gl.GL_TEXTURE_BUFFER, self.texture_buffer[1])
        gl.glTexBuffer(gl.GL_TEXTURE_BUFFER, gl.GL_R32I, self.texture_buffer[1])

    def _set_voxel(self, x: int, y: int, z: int, pos: "Vec3", tex: int, active: bool):
        if x > self.width or y > self.height or z > self.depth:
            raise ValueError("Invalid voxel position")
        index = x + y * self.width + z * self.width * self.height
        self.voxel_positions[index] = pos
        self.is_active[index] = active
        self.texture_index[index] = tex
