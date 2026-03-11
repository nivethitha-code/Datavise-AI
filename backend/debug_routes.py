from main import app
for route in app.routes:
    if hasattr(route, "path"):
        methods = getattr(route, "methods", "N/A")
        print(f"{methods} {route.path}")