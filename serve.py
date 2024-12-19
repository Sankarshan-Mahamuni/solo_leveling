from waitress import serve
import app  # This assumes your Flask app is in a module named app

if __name__ == "__main__":
    serve(app.app, host='0.0.0.0', port=8080)
