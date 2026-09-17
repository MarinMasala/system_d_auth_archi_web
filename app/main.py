from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)