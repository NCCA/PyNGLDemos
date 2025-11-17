struct VertexIn
{
    @location(0) position: vec3<f32>,
};

struct VertexOut
{
    @builtin(position) position: vec4<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut
{
    var output: VertexOut;
    output.position = vec4<f32>(input.position, 1.0);
    return output;
}


@fragment
fn fragment_main() -> @location(0) vec4<f32>
{
    return vec4<f32>(1.0, 0.0, 0.0, 1.0); // Red colour
}
