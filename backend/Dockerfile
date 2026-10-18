FROM python:3.13-slim

WORKDIR /app

# Salin requirements.txt terlebih dahulu untuk memanfaatkan cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi
COPY . .

# Railway akan menyuntikkan variabel PORT secara otomatis
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]