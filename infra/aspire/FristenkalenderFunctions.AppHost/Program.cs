var builder = DistributedApplication.CreateBuilder(args);

// Reference the Python FastAPI app using its Dockerfile
// The context path is relative to the AppHost project directory (../../..)
var api = builder.AddDockerfile("fristenkalender-api", contextPath: "../../..")
    .WithHttpEndpoint(port: 80, targetPort: 80, name: "http")
    .WithExternalHttpEndpoints();

builder.Build().Run();
