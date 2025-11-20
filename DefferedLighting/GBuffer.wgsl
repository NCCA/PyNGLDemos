// Physically Based Rendering (PBR) shader, translated from GLSL.
// Original GLSL code based on https://learnopengl.com/#!PBR/Lighting

// Vertex Shader

struct TransformUniforms {
    MVP : mat4x4<f32>,
    normalMatrix : mat4x4<f32>,
    M : mat4x4<f32>,
};
@group(0) @binding(0) var<uniform> transforms : TransformUniforms;

struct VertexIn {
    @location(0) position: vec3<f32>,
    @location(1) normal: vec3<f32>,
    @location(2) uv: vec2<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) worldPos: vec3<f32>,
    @location(1) normal: vec3<f32>,
    @location(2) uv: vec2<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.worldPos = (transforms.M * vec4<f32>(input.position, 1.0)).xyz;
    output.normal = normalize((transforms.normalMatrix * vec4<f32>(input.normal, 0.0)).xyz);
    output.position = transforms.MVP * vec4<f32>(input.position, 1.0);
    output.uv = input.uv;
    return output;
}

// Fragment Shader

struct MaterialParams {
    albedo: vec3<f32>,
    metallic: f32,
    roughness: f32,
    ao: f32,
};
@group(1) @binding(0) var<uniform> material: MaterialParams;

struct GBufferOutput {
    @location(0) position: vec4<f32>,
    @location(1) normal: vec4<f32>,
    @location(2) albedo: vec4<f32>,
};


@fragment
fn fragment_main(in: VertexOut) -> GBufferOutput {
    var output: GBufferOutput;
    output.position = vec4<f32>(in.worldPos, material.ao);
    output.normal = vec4<f32>(normalize(in.normal), material.roughness);
    output.albedo = vec4<f32>(material.albedo, material.metallic);
    return output;
}
