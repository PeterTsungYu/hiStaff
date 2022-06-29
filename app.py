# library
from flask import Flask


def init_app():
    app = Flask(__name__)
    with app.app_context():
        import routes
        import dashboard
        
        app = dashboard.init_dashboard(app)
        
        return app

app = init_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003,)