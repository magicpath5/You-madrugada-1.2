#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import HTTPServer, SimpleHTTPRequestHandler
from email.parser import BytesParser
from email import policy
import os
import json
from pathlib import Path

# Pasta onde os arquivos serão salvos
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'envios')

# Criar pasta se não existir
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Servir arquivos estáticos (index.html, etc)
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/list':
            # Listar arquivos da pasta envios
            try:
                files = []
                if os.path.exists(UPLOAD_DIR):
                    for filename in os.listdir(UPLOAD_DIR):
                        filepath = os.path.join(UPLOAD_DIR, filename)
                        if os.path.isfile(filepath):
                            files.append({
                                'name': filename,
                                'path': os.path.join('envios', filename),
                                'type': filename.split('.')[-1].lower()
                            })
                
                response = json.dumps(files).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(response))
                self.end_headers()
                self.wfile.write(response)
                return
            except Exception as e:
                self.send_error(500, f"Erro ao listar arquivos: {str(e)}")
                return
        
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/upload':
            # Processar upload
            content_type = self.headers['Content-Type']
            
            if 'multipart/form-data' in content_type:
                try:
                    # Ler tamanho do conteúdo
                    content_length = int(self.headers['Content-Length'])
                    body = self.rfile.read(content_length)
                    
                    # Parsear multipart
                    boundary = content_type.split("boundary=")[1].encode()
                    
                    # Dividir partes
                    parts = body.split(b'--' + boundary)
                    
                    for part in parts:
                        if b'filename=' in part:
                            # Extrair nome do arquivo
                            filename_start = part.find(b'filename="') + 10
                            filename_end = part.find(b'"', filename_start)
                            filename = part[filename_start:filename_end].decode('utf-8')
                            
                            # Extrair conteúdo do arquivo
                            file_data = part.split(b'\r\n\r\n')[1].rsplit(b'\r\n', 1)[0]
                            
                            # Salvar arquivo
                            filepath = os.path.join(UPLOAD_DIR, filename)
                            with open(filepath, 'wb') as f:
                                f.write(file_data)
                            
                            # Retornar resposta de sucesso
                            response = json.dumps({
                                'status': 'success',
                                'path': os.path.join('envios', filename),
                                'filename': filename
                            }).encode('utf-8')
                            
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.send_header('Content-Length', len(response))
                            self.end_headers()
                            self.wfile.write(response)
                            return
                    
                    self.send_error(400, "Nenhum arquivo enviado")
                        
                except Exception as e:
                    print(f"Erro ao processar upload: {e}")
                    self.send_error(500, f"Erro no servidor: {str(e)}")
            else:
                self.send_error(400, "Content-Type inválido")
        else:
            self.send_error(404, "Rota não encontrada")

    def end_headers(self):
        # Adicionar headers CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        SimpleHTTPRequestHandler.end_headers(self)

if __name__ == '__main__':
    PORT = 1100
    Handler = UploadHandler
    httpd = HTTPServer(('localhost', PORT), Handler)

    print(f"Servidor rodando em http://localhost:{PORT}")
    print(f"Arquivos serão salvos em: {UPLOAD_DIR}")
    print("Pressione Ctrl+C para parar o servidor")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")
        httpd.shutdown()
