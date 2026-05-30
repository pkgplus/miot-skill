from .auth import routes as auth_routes
from .devices import routes as device_routes
from .scenes import routes as scene_routes
from .homes import routes as home_routes


def all_api_routes():
    return auth_routes + device_routes + scene_routes + home_routes
