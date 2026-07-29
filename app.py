import os
import re
from flask import Flask, jsonify, render_template, request
from PIL import Image
from pypdf import PdfWriter
from yt_dlp import YoutubeDL

app = Flask(__name__)


class YouTubeDownloader:

    def __init__(self, output_path: str):
        self.output_path = output_path
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def validar_url(self, url: str) -> bool:
        regex_youtube = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"
        return bool(re.match(regex_youtube, url))

    def obter_configuracoes_ytdlp(self) -> dict:
        return {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(self.output_path, "%(title)s.%(ext)s"),
            "restrictfilenames": True,
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                },
                {"key": "FFmpegMetadata", "add_metadata": True},
            ],
            "quiet": True,
        }

    def baixar_mp3(self, url: str):
        if not self.validar_url(url):
            return False, "URL inválida do YouTube."

        ydl_opts = self.obter_configuracoes_ytdlp()
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                titulo = info.get("title", "Áudio")
                return True, f'Música "{titulo}" baixada em Downloads!'
        except Exception as e:
            return False, f"Erro ao baixar: {str(e)}"


# Rota Principal
@app.route("/")
def index():
    return render_template("index.html")


# Rota 1: Imagem para PDF
@app.route("/api/converter-imagem", methods=["POST"])
def converter_imagem():
    if "imagem" not in request.files:
        return jsonify(
            {"sucesso": False, "mensagem": "Nenhuma imagem enviada."}
        )

    arquivo = request.files["imagem"]
    if arquivo.filename == "":
        return jsonify(
            {"sucesso": False, "mensagem": "Nenhum arquivo selecionado."}
        )

    try:
        img = Image.open(arquivo.stream)
        img_rgb = img.convert("RGB")

        pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        nome_saida = (
            os.path.splitext(arquivo.filename)[0] + "_convertido.pdf"
        )
        caminho_final = os.path.join(pasta_downloads, nome_saida)

        img_rgb.save(caminho_final)
        return jsonify(
            {
                "sucesso": True,
                "mensagem": f"Salvo em Downloads como {nome_saida}",
            }
        )
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": str(e)})


# Rota 2: Mesclar PDFs
@app.route("/api/mesclar-pdfs", methods=["POST"])
def mesclar_pdfs():
    arquivos = request.files.getlist("pdfs")
    nome_personalizado = request.form.get("nome_pdf", "").strip()

    if not arquivos or len(arquivos) < 2:
        return jsonify(
            {
                "sucesso": False,
                "mensagem": "Selecione pelo menos 2 arquivos PDF.",
            }
        )

    if not nome_personalizado:
        nome_saida = "PDF_Mesclado.pdf"
    else:
        nome_saida = (
            nome_personalizado
            if nome_personalizado.lower().endswith(".pdf")
            else f"{nome_personalizado}.pdf"
        )

    try:
        merger = PdfWriter()
        for pdf in arquivos:
            merger.append(pdf.stream)

        pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        caminho_final = os.path.join(pasta_downloads, nome_saida)

        with open(caminho_final, "wb") as arquivo_saida:
            merger.write(arquivo_saida)
        merger.close()

        return jsonify(
            {
                "sucesso": True,
                "mensagem": f'PDFs mesclados em Downloads como "{nome_saida}"!',
            }
        )
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": str(e)})


# Rota 3: Baixar MP3 do YouTube
@app.route("/api/baixar-mp3", methods=["POST"])
def baixar_mp3():
    url = request.form.get("url", "").strip()
    if not url:
        return jsonify({"sucesso": False, "mensagem": "Informe a URL do vídeo."})

    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    downloader = YouTubeDownloader(output_path=pasta_downloads)

    sucesso, mensagem = downloader.baixar_mp3(url)
    return jsonify({"sucesso": sucesso, "mensagem": mensagem})


if __name__ == "__main__":
    app.run(debug=True, port=5000)