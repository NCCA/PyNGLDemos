#version 410 core

layout(points) in;
layout(triangle_strip, max_vertices = 36) out;
flat in int textureIndex[];
flat in int vertexID[];
flat in int activeVoxel[];
flat out int vertID;
flat out int isactive;

uniform mat4 MVP;
uniform ivec2 textureAtlasDims;
out vec2 textureCoords;

vec2 getTileUV(int index)
{
    int tilesPerRow = textureAtlasDims.x;
    int tileX = index % tilesPerRow;
    int tileY = index / tilesPerRow;
    return vec2(tileX, tileY) / vec2(textureAtlasDims);
}

void emitFace(vec3 center, vec3 normal, vec3 up)
{
    vec3 right = normalize(cross(up, normal)) * 0.5;
    up = normalize(up) * 0.5;

    vec2 tileSize = 1.0 / vec2(textureAtlasDims);
    vec2 uvMin = getTileUV(textureIndex[0]);
    vec2 uvMax = uvMin + tileSize;

    vec2 uvs[4] = vec2[4](uvMin, vec2(uvMax.s, uvMin.t), vec2(uvMin.s, uvMax.t), uvMax);
    vec3 corners[4];
    corners[0] = center - right - up;
    corners[1] = center + right - up;
    corners[2] = center - right + up;
    corners[3] = center + right + up;

    for (int i = 0; i < 4; ++i)
    {
        gl_Position = MVP * vec4(corners[i], 1.0);
        textureCoords = uvs[i];
        vertID = vertexID[0];
        isactive = activeVoxel[0];
        EmitVertex();
    }
    EndPrimitive();
}

void main()
{
    vec3 center = gl_in[0].gl_Position.xyz;

    emitFace(center + vec3(0.5, 0.0, 0.0), vec3(1, 0, 0), vec3(0, 1, 0)); // +X
    emitFace(center - vec3(0.5, 0.0, 0.0), vec3(-1, 0, 0), vec3(0, 1, 0)); // -X
    emitFace(center + vec3(0.0, 0.5, 0.0), vec3(0, 1, 0), vec3(0, 0, 1)); // +Y
    emitFace(center - vec3(0.0, 0.5, 0.0), vec3(0, -1, 0), vec3(0, 0, 1)); // -Y
    emitFace(center + vec3(0.0, 0.0, 0.5), vec3(0, 0, 1), vec3(0, 1, 0)); // +Z
    emitFace(center - vec3(0.0, 0.0, 0.5), vec3(0, 0, -1), vec3(0, 1, 0)); // -Z
}
