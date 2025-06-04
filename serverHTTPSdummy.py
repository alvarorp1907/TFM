import http.server
import ssl

CERT_SERVER_DIR = "./serverCertificates/"
CERT_CA_DIR = "./CAcertificates/"

def get_ssl_context(certfile, keyfile):
    certfile = CERT_SERVER_DIR + certfile
    keyfile = CERT_SERVER_DIR + keyfile
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(certfile, keyfile)
    context.set_ciphers("@SECLEVEL=1:ALL")
    
    # Requerir certificados de cliente
    context.verify_mode = ssl.CERT_REQUIRED
    # Cargar la CA que firmó los certificados de los clientes
    context.load_verify_locations(cafile=CERT_CA_DIR + "ca.cert")
    
    return context


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        print(post_data.decode("utf-8"))

if __name__ == "__main__":
  server_address = ("127.0.0.1", 5000)
  httpd = http.server.HTTPServer(server_address, MyHandler)
  
  context = get_ssl_context("server.cert", "server.key")
  httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
  
  print(f"HTTPS server running in {server_address}")
  httpd.serve_forever()