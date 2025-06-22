from openvino.runtime import Core
core = Core()
model = core.read_model("best.xml")
compiled_model = core.compile_model(model, "CPU")
print("Model loaded successfully!")
