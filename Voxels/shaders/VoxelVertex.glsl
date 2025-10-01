#version 410 core
uniform samplerBuffer posSampler; // index 1
uniform isamplerBuffer texIndexSampler; // index 2
uniform isamplerBuffer isActiveSampler; // index 3

flat out int textureIndex;
flat out int vertexID;
flat out int activeVoxel;
void main()
{
    vec3 inputData = texelFetch(posSampler, gl_VertexID).xyz;
    textureIndex = texelFetch(texIndexSampler, gl_VertexID).r;
    activeVoxel = texelFetch(isActiveSampler, gl_VertexID).r;

    vertexID = gl_VertexID;
    gl_Position = vec4(inputData, 1.0);
}
