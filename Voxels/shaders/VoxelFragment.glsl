#version 410 core

layout(location = 0) out vec4 outColour;
layout(location = 1) out vec4 indexID;
flat in int isactive;
in vec2 textureCoords;
flat in int vertID;
uniform sampler2D textureSampler;

vec4 encodeIDToRGBA(int id) {
    uint uid = uint(id);
    return vec4(
        float((uid >> 24u) & 0xFFu) / 255.0,
        float((uid >> 16u) & 0xFFu) / 255.0,
        float((uid >> 8u) & 0xFFu) / 255.0,
        float(uid & 0xFFu) / 255.0
    );
}

void main()
{
    if (isactive == 0)
        discard;
    outColour = texture(textureSampler, textureCoords);
    indexID = encodeIDToRGBA(vertID);
}
