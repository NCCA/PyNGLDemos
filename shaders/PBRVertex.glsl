#version 410 core
// this demo is based on code from here https://learnopengl.com/#!PBR/Lighting
/// @brief the vertex passed in
layout (location = 0) in vec3 inVert;
/// @brief the normal passed in
layout (location = 1) in vec3 inNormal;
/// @brief the in uv
layout (location = 2) in vec2 inUV;

out vec3 worldPos;
out vec3 normal;


uniform mat4 MVP;
uniform mat4 normalMatrix;
uniform mat4 M;

void main()
{
  worldPos = vec3(M * vec4(inVert, 1.0f));
  normal=normalize(mat3(normalMatrix)*inNormal);
  gl_Position = MVP*vec4(inVert,1.0);
}

