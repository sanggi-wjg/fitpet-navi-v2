from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from fitpet_navi.controller.health.health_controller import health_router
from fitpet_navi.controller.support.exception_handler import register_exception_handlers
from fitpet_navi.controller.task.task_controller import task_router
from fitpet_navi.core.log import setup_logging
from fitpet_navi.core.middleware import RequestIdMiddleware

setup_logging()


app = FastAPI()
app.add_middleware(GZipMiddleware)
app.add_middleware(RequestIdMiddleware)
register_exception_handlers(app)

app.include_router(health_router)
app.include_router(task_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        port=9000,
        reload=False,
        use_colors=True,
    )
