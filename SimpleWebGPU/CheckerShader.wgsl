
// simple checker shader
struct TransformUniforms {
    MVP : mat4x4<f32>,
    normalMatrix : mat4x4<f32>,
};
@group(0) @binding(0) var<uniform> transforms : TransformUniforms;

struct VertexIn {
    @location(0) position: vec3<f32>,
    @location(1) normal: vec3<f32>,
    @location(2) uv: vec2<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) uv: vec2<f32>,
    @location(1) normal: vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.uv = input.uv;
    output.normal = normalize((transforms.normalMatrix * vec4<f32>(input.normal, 0.0)).xyz);
    output.position = transforms.MVP * vec4<f32>(input.position, 1.0);
    return output;
}

// Fragment Shader

struct MaterialParams {
    colour1: vec4<f32>,
    colour2: vec4<f32>,
    checkSize: f32,
    checkOn: u32,
};
@group(1) @binding(0) var<uniform> material: MaterialParams;

struct LightParams {
    lightPosition: vec3<f32>,
    lightColor: vec3<f32>,
};
@group(1) @binding(1) var<uniform> light: LightParams;


fn checker(uv: vec2<f32>) -> vec4<f32>
{
    if (material.checkOn == 0u)
    {
        return material.colour1;
    }
    else
    {
        let v_int = i32(floor(material.checkSize * uv.x)) + i32(floor(material.checkSize * uv.y));
        if (v_int % 2 == 0)
        {
            return material.colour2;
        }
        else
        {
            return material.colour1;
        }
    }
}

@fragment
fn fragment_main(in: VertexOut) -> @location(0) vec4<f32>
{

    let colour = checker(in.uv);
    let N = normalize(in.normal);
    let L = normalize(light.lightPosition);
    let diffuse = max(dot(N, L), 0.0);
    return vec4<f32>(colour.rgb * light.lightColor * diffuse, colour.a);

}
