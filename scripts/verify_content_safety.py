"""Local Chrome smoke check: render hostile synthetic email text, never query a DB.

Use --chrome /path/to/chrome on other platforms. Requires a local Chrome binary.
No participant records or database connections are used.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome', default='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    args = parser.parse_args()
    if not Path(args.chrome).is_file():
        raise RuntimeError('Configure an installed Chrome executable with --chrome.')
    import app as application
    from flask import render_template
    # Fail if a rendering change unexpectedly attempts database access.
    def forbidden_connection():
        raise RuntimeError('Browser content verification must not connect to a database.')
    application.get_db_connection = forbidden_connection
    requests = []
    rendered = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith('/unsafe-resource'):
                requests.append(self.path)
            self.send_response(200 if self.path == '/' else 404)
            for key, value in rendered['headers']:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(rendered['body'] if self.path == '/' else b'')

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    origin = 'http://127.0.0.1:'+str(server.server_port)
    attack = ('<script>document.body.setAttribute("data-phishsense-executed","yes")</script>'
              '<img src="'+origin+'/unsafe-resource/image" onerror="alert(1)">'
              '<iframe src="'+origin+'/unsafe-resource/frame"></iframe>'
              '<style>@import url("'+origin+'/unsafe-resource/css");</style>'
              '<a href="javascript:alert(2)">Synthetic link</a>'
              '\n[[link:Review employee statement|https://payroll.evercrest-group.example/statement]]'
              '\n[[attachment:statement.pdf]]')
    scenario = dict(scenario_id=1, sender_name=attack, sender_email='synthetic@example.invalid',
                    subject=attack, email_body=attack, training_context=attack)
    try:
        with application.app.test_request_context('/'):
            response = application.app.make_response(render_template('training.html',
                scenario=scenario, username='Synthetic browser check', form_token='synthetic-only'))
            response = application.app.process_response(response)
            rendered.update(body=response.get_data(), headers=list(response.headers.items()))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix='phishsense-chrome-') as profile:
                result = subprocess.run([args.chrome, '--headless', '--disable-gpu',
                    '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
                    '--disable-component-update', '--disable-sync', '--user-data-dir='+profile,
                    '--timeout=10000', '--dump-dom', origin+'/'],
                    capture_output=True, text=True, timeout=45)
            if result.returncode:
                raise RuntimeError('Chrome content verification did not complete.')
            dom = result.stdout
            assert '<body data-phishsense-executed=' not in dom
            assert '<script>' not in dom and '<iframe' not in dom and '<img src=' not in dom
            assert '&lt;script&gt;' in dom
            assert 'Review employee statement' in dom and 'Destination: https://payroll.evercrest-group.example/statement' in dom
            assert 'href="https://payroll.evercrest-group.example' not in dom
            assert 'statement.pdf' in dom
            assert not requests
            print('Chrome content verification passed: hostile text escaped, no injected script/frame/image, zero unsafe-resource requests.')
            print('No database connections or record changes performed.')
        finally:
            server.shutdown()
            thread.join(timeout=5)
    finally:
        server.server_close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Browser verification stopped. Error type:', type(error).__name__)
        raise SystemExit(1)
