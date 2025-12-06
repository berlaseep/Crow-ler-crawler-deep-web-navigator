"""
Crow-ler - Deep Web Navigator con Interfaz Gráfica y Configuración Automática
Versión 2.0 - Con instalación automática de dependencias
"""

import sys
import subprocess
import os
from pathlib import Path

# ============================================
# INSTALACIÓN AUTOMÁTICA DE DEPENDENCIAS
# ============================================

def install_package(package):
    """Instala un paquete de Python usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
        return True
    except:
        return False

def check_and_install_dependencies():
    """Verifica e instala todas las dependencias necesarias"""
    required_packages = {
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'psycopg2': 'psycopg2-binary',
        'tkinter': None  # tkinter viene con Python
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            if package:
                missing.append(package)
    
    if missing:
        print("Instalando dependencias faltantes...")
        for package in missing:
            print(f"  - Instalando {package}...")
            if install_package(package):
                print(f"    ✓ {package} instalado")
            else:
                print(f"    ✗ Error instalando {package}")
        print("Dependencias instaladas. Reiniciando...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

# Ejecutar instalación antes de importar
check_and_install_dependencies()

# Ahora importar todo
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import requests
from bs4 import BeautifulSoup
import time
import psycopg2
from psycopg2 import sql
from urllib.parse import urljoin, urlparse
import json
import zipfile
import urllib.request
import platform
import shutil

# ============================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================

class Config:
    # Tor
    TOR_PORT = 9050
    TOR_PROXY = f"socks5h://127.0.0.1:{TOR_PORT}"
    
    # PostgreSQL
    DB_HOST = "localhost"
    DB_NAME = "crowler_db"
    DB_USER = "postgres"
    DB_PASS = "postgres"
    DB_PORT = "5432"
    
    # Crow-ler
    REQUEST_TIMEOUT = 20
    MAX_LINKS_PER_DOMAIN = 15
    DELAY_BETWEEN_REQUESTS = 2
    
    # Directorios
    BASE_DIR = Path.home() / "Crow-ler"
    TOR_DIR = BASE_DIR / "tor"
    DATA_DIR = BASE_DIR / "data"
    
    # Icono
    ICON_PATH = r"M:\Usuario\Desktop\X\Herramientas\Amateur\crow-ler\images\crow-lericono.ico"
    
    # URL Semilla
    SEED_URL = "http://wkkrcvje42625v7g77maufsgvqbu7eh7tgfvwzqrarqptfktqiaa6ayd.onion/darkweb-search-engines-v3/hidden-wiki"
    
    # Colores tema oscuro dorado
    BG_COLOR = "#1a1a1a"          # Negro profundo
    FG_COLOR = "#d4af37"           # Dorado
    BG_SECONDARY = "#2d2d2d"       # Gris oscuro
    BUTTON_BG = "#d4af37"          # Dorado
    BUTTON_FG = "#000000"          # Negro para contraste
    ENTRY_BG = "#3d3d3d"           # Gris medio
    SUCCESS_COLOR = "#ffd700"      # Dorado brillante
    ERROR_COLOR = "#ff6b6b"        # Rojo suave
    WARNING_COLOR = "#ffb347"      # Naranja dorado

# ============================================
# INSTALADOR AUTOMÁTICO
# ============================================

class AutoInstaller:
    """Maneja la instalación automática de Tor y PostgreSQL"""
    
    @staticmethod
    def create_directories():
        """Crea los directorios necesarios"""
        Config.BASE_DIR.mkdir(parents=True, exist_ok=True)
        Config.TOR_DIR.mkdir(parents=True, exist_ok=True)
        Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return True
    
    @staticmethod
    def download_file(url, destination, callback=None):
        """Descarga un archivo con barra de progreso"""
        try:
            response = urllib.request.urlopen(url)
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        callback(progress)
            return True
        except Exception as e:
            print(f"Error descargando: {e}")
            return False
    
    @staticmethod
    def install_tor_windows(callback=None):
        """Instala Tor Expert Bundle en Windows"""
        tor_url = "https://archive.torproject.org/tor-package-archive/torbrowser/12.5.6/tor-expert-bundle-windows-x86_64-12.5.6.tar.gz"
        tor_zip = Config.TOR_DIR / "tor.tar.gz"
        
        if callback:
            callback("Descargando Tor Expert Bundle...")
        
        if not AutoInstaller.download_file(tor_url, tor_zip, 
            lambda p: callback(f"Descargando Tor: {p:.1f}%") if callback else None):
            return False
        
        if callback:
            callback("Extrayendo Tor...")
        
        try:
            import tarfile
            with tarfile.open(tor_zip, 'r:gz') as tar:
                tar.extractall(Config.TOR_DIR)
            tor_zip.unlink()
            return True
        except Exception as e:
            print(f"Error extrayendo Tor: {e}")
            return False
    
    @staticmethod
    def install_postgresql_windows(callback=None):
        """Instala PostgreSQL portable en Windows"""
        if callback:
            callback("PostgreSQL requiere instalación manual.\nDescarga desde: https://www.postgresql.org/download/windows/")
        return False
    
    @staticmethod
    def check_tor_installed():
        """Verifica si Tor está instalado"""
        possible_paths = [
            Config.TOR_DIR / "tor" / "tor.exe",
            Config.TOR_DIR / "Tor" / "tor.exe",
            "tor.exe",
            "/usr/bin/tor"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        return None
    
    @staticmethod
    def check_postgresql_installed():
        """Verifica si PostgreSQL está instalado y corriendo"""
        try:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASS,
                port=Config.DB_PORT,
                connect_timeout=3
            )
            conn.close()
            return True
        except:
            return False

# ============================================
# GESTOR DE BASE DE DATOS
# ============================================

class DatabaseManager:
    """Maneja todas las operaciones con PostgreSQL"""
    
    @staticmethod
    def get_connection():
        """Obtiene conexión a la base de datos"""
        try:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASS,
                port=Config.DB_PORT
            )
            return conn
        except Exception as e:
            raise Exception(f"Error conectando a PostgreSQL: {e}")
    
    @staticmethod
    def create_database():
        """Crea la base de datos si no existe"""
        try:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASS,
                port=Config.DB_PORT
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (Config.DB_NAME,))
            if not cursor.fetchone():
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(Config.DB_NAME)))
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error creando base de datos: {e}")
            return False
    
    @staticmethod
    def init_tables():
        """Inicializa las tablas necesarias"""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # Tabla: Cola principal
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queue (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE
            );
        ''')
        
        # Tabla: Páginas crow-leadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crowled_pages (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                status_code INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Tabla: Cola de reintentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS retry_queue (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE
            );
        ''')
        
        # Tabla: Estadísticas de dominio
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_stats (
                domain TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            );
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_stats():
        """Obtiene estadísticas de la base de datos"""
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM queue")
        queue_size = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM retry_queue")
        retry_size = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crowled_pages WHERE title IS NOT NULL")
        crowled_size = cursor.fetchone()[0]
        
        conn.close()
        return queue_size, retry_size, crowled_size

# ============================================
# CROW-LER ENGINE
# ============================================

class CrowlerEngine:
    """Motor del crow-ler"""
    
    def __init__(self, gui_callback=None):
        self.running = False
        self.gui_callback = gui_callback
        self.proxies = {
            'http': Config.TOR_PROXY,
            'https': Config.TOR_PROXY
        }
    
    def log(self, message):
        """Envía mensaje al GUI"""
        if self.gui_callback:
            self.gui_callback(message)
        print(message)
    
    @staticmethod
    def get_domain(url):
        try:
            return urlparse(url).netloc
        except:
            return None
    
    @staticmethod
    def is_onion_link(url):
        try:
            parsed = urlparse(url)
            return parsed.netloc.endswith('.onion')
        except:
            return False
    
    def add_url_to_queue(self, conn, url):
        """Agrega URL a la cola principal"""
        domain = self.get_domain(url)
        if not domain:
            return False
        
        cursor = conn.cursor()
        
        # Verificar si ya fue crow-leada
        cursor.execute("SELECT 1 FROM crowled_pages WHERE url = %s", (url,))
        if cursor.fetchone():
            return False
        
        # Verificar límite de dominio
        cursor.execute("SELECT count FROM domain_stats WHERE domain = %s", (domain,))
        row = cursor.fetchone()
        current_count = row[0] if row else 0
        
        if current_count >= Config.MAX_LINKS_PER_DOMAIN:
            return False
        
        try:
            cursor.execute("INSERT INTO queue (url) VALUES (%s) ON CONFLICT DO NOTHING", (url,))
            
            if cursor.rowcount > 0:
                cursor.execute("""
                    INSERT INTO domain_stats (domain, count) VALUES (%s, 1)
                    ON CONFLICT (domain) DO UPDATE SET count = domain_stats.count + 1
                """, (domain,))
                conn.commit()
                return True
            
            conn.rollback()
            return False
        except Exception:
            conn.rollback()
            return False
    
    def get_next_url(self, conn, mode="NORMAL"):
        """Obtiene la siguiente URL de la cola"""
        cursor = conn.cursor()
        
        try:
            if mode == "NORMAL":
                query = sql.SQL("""
                    DELETE FROM queue
                    WHERE id = (
                        SELECT id FROM queue ORDER BY id ASC FOR UPDATE SKIP LOCKED LIMIT 1
                    )
                    RETURNING id, url;
                """)
                
                cursor.execute(query)
                row = cursor.fetchone()
                
                if row:
                    url_id, url = row
                    cursor.execute("INSERT INTO crowled_pages (url, status_code) VALUES (%s, 0) ON CONFLICT DO NOTHING", (url,))
                    conn.commit()
                    return url, url_id
            
            elif mode == "RETRY":
                cursor.execute("SELECT id, url FROM retry_queue ORDER BY id ASC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    return row[1], row[0]
            
            conn.commit()
            return None, None
        
        except Exception as e:
            conn.rollback()
            self.log(f"Error obteniendo URL: {e}")
            return None, None
    
    def update_page_title(self, conn, url, title, status_code):
        """Actualiza información de la página"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE crowled_pages 
                SET title = %s, status_code = %s 
                WHERE url = %s
            """, (title, status_code, url))
            conn.commit()
        except Exception:
            conn.rollback()
    
    def crowl(self, mode="NORMAL"):
        """Función principal del crow-ler"""
        self.running = True
        
        try:
            conn = DatabaseManager.get_connection()
            
            # Insertar semilla si la DB está vacía
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crowled_pages")
            if cursor.fetchone()[0] == 0:
                cursor.execute("SELECT COUNT(*) FROM queue")
                if cursor.fetchone()[0] == 0:
                    self.log("Insertando URL semilla...")
                    self.add_url_to_queue(conn, Config.SEED_URL)
            
            self.log(f"Iniciando crow-ler en modo: {mode}")
            
            while self.running:
                current_url, url_id = self.get_next_url(conn, mode)
                
                if not current_url:
                    self.log(f"No hay más URLs en la cola ({mode})")
                    break
                
                # Obtener estadísticas
                q_size, r_size, c_size = DatabaseManager.get_stats()
                self.log(f"\n[Cola: {q_size} | 404s: {r_size} | OK: {c_size}]")
                self.log(f"Visitando: {current_url}")
                
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
                    }
                    
                    response = requests.get(
                        current_url, 
                        proxies=self.proxies, 
                        headers=headers, 
                        timeout=Config.REQUEST_TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_title = soup.title.string.strip() if soup.title else "Sin título"
                        
                        self.log(f"✓ Título: {page_title}")
                        self.update_page_title(conn, current_url, page_title, 200)
                        
                        # Guardar en archivo
                        output_file = Config.DATA_DIR / "onion_links.txt"
                        with open(output_file, "a", encoding="utf-8") as f:
                            f.write(f"TÍTULO: {page_title}\nURL: {current_url}\n{'-'*50}\n")
                        
                        # Extraer enlaces
                        links_found = 0
                        new_links = 0
                        
                        for link in soup.find_all('a', href=True):
                            raw_url = link['href']
                            full_url = urljoin(current_url, raw_url).split('#')[0]
                            
                            if self.is_onion_link(full_url):
                                if self.add_url_to_queue(conn, full_url):
                                    new_links += 1
                                links_found += 1
                        
                        self.log(f"Enlaces encontrados: {links_found} | Nuevos: {new_links}")
                    
                    elif response.status_code == 404:
                        self.log("✗ Error 404")
                        self.update_page_title(conn, current_url, "ERROR 404", 404)
                        
                        if mode == "NORMAL":
                            cursor.execute("INSERT INTO retry_queue (url) VALUES (%s) ON CONFLICT DO NOTHING", (current_url,))
                            conn.commit()
                    
                    else:
                        self.log(f"✗ Status: {response.status_code}")
                        self.update_page_title(conn, current_url, f"ERROR {response.status_code}", response.status_code)
                
                except requests.exceptions.Timeout:
                    self.log("✗ Timeout")
                    self.update_page_title(conn, current_url, "TIMEOUT", 0)
                
                except requests.exceptions.ConnectionError:
                    self.log("✗ Error de conexión")
                    self.update_page_title(conn, current_url, "CONN ERROR", 0)
                
                except Exception as e:
                    self.log(f"✗ Error: {str(e)[:50]}")
                
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            
            conn.close()
            self.log("\nCrow-ler detenido")
        
        except Exception as e:
            self.log(f"Error crítico: {e}")
        
        finally:
            self.running = False
    
    def stop(self):
        """Detiene el crow-ler"""
        self.running = False

# ============================================
# INTERFAZ GRÁFICA
# ============================================

class CrowlerGUI:
    """Interfaz gráfica principal"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Crow-ler v2.0 - Deep Web Navigator")
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        
        # Intentar cargar el icono
        try:
            if os.path.exists(Config.ICON_PATH):
                self.root.iconbitmap(Config.ICON_PATH)
        except:
            pass
        
        # Configurar tema oscuro
        self.setup_theme()
        
        self.crowler = None
        self.crowler_thread = None
        self.tor_process = None
        
        self.create_widgets()
        self.check_requirements()
    
    def setup_theme(self):
        """Configura el tema oscuro con dorado"""
        self.root.configure(bg=Config.BG_COLOR)
        
        # Estilo para ttk
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores para widgets ttk
        style.configure('TFrame', background=Config.BG_COLOR)
        style.configure('TLabelframe', background=Config.BG_COLOR, foreground=Config.FG_COLOR, 
                       bordercolor=Config.FG_COLOR, borderwidth=2)
        style.configure('TLabelframe.Label', background=Config.BG_COLOR, foreground=Config.FG_COLOR,
                       font=('Segoe UI', 10, 'bold'))
        style.configure('TLabel', background=Config.BG_COLOR, foreground=Config.FG_COLOR,
                       font=('Segoe UI', 9))
        style.configure('TButton', background=Config.BUTTON_BG, foreground=Config.BUTTON_FG,
                       borderwidth=0, font=('Segoe UI', 9, 'bold'))
        style.map('TButton', background=[('active', Config.SUCCESS_COLOR)])
        style.configure('TEntry', fieldbackground=Config.ENTRY_BG, foreground=Config.FG_COLOR,
                       borderwidth=1, insertcolor=Config.FG_COLOR)
        style.configure('TRadiobutton', background=Config.BG_COLOR, foreground=Config.FG_COLOR,
                       font=('Segoe UI', 9))
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # Frame superior: Estado del sistema
        status_frame = ttk.LabelFrame(self.root, text="⚙ ESTADO DEL SISTEMA", padding=15)
        status_frame.pack(fill="x", padx=15, pady=10)
        
        self.tor_status = ttk.Label(status_frame, text="Tor: Verificando...", 
                                    font=('Segoe UI', 10, 'bold'))
        self.tor_status.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.db_status = ttk.Label(status_frame, text="PostgreSQL: Verificando...",
                                   font=('Segoe UI', 10, 'bold'))
        self.db_status.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Button(status_frame, text="🔍 Verificar", command=self.check_requirements).grid(
            row=0, column=2, padx=10, pady=5)
        ttk.Button(status_frame, text="📥 Instalar", command=self.install_dependencies).grid(
            row=0, column=3, padx=10, pady=5)
        
        # Frame de configuración
        config_frame = ttk.LabelFrame(self.root, text="⚙ CONFIGURACIÓN", padding=15)
        config_frame.pack(fill="x", padx=15, pady=10)
        
        ttk.Label(config_frame, text="URL Semilla:", font=('Segoe UI', 10)).grid(
            row=0, column=0, sticky="w", pady=5)
        self.seed_entry = ttk.Entry(config_frame, width=80, font=('Consolas', 9))
        self.seed_entry.insert(0, Config.SEED_URL)
        self.seed_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(config_frame, text="Modo:", font=('Segoe UI', 10)).grid(
            row=1, column=0, sticky="w", pady=5)
        
        mode_frame = ttk.Frame(config_frame)
        mode_frame.grid(row=1, column=1, sticky="w", pady=5)
        
        self.mode_var = tk.StringVar(value="NORMAL")
        ttk.Radiobutton(mode_frame, text="🔄 Normal", variable=self.mode_var, 
                       value="NORMAL").pack(side="left", padx=10)
        ttk.Radiobutton(mode_frame, text="🔁 Reintentos", variable=self.mode_var, 
                       value="RETRY").pack(side="left", padx=10)
        
        # Frame de estadísticas
        stats_frame = ttk.LabelFrame(self.root, text="📊 ESTADÍSTICAS", padding=15)
        stats_frame.pack(fill="x", padx=15, pady=10)
        
        self.queue_label = ttk.Label(stats_frame, text="Cola: 0", 
                                     font=('Segoe UI', 11, 'bold'))
        self.queue_label.grid(row=0, column=0, padx=20, pady=5)
        
        self.retry_label = ttk.Label(stats_frame, text="Reintentos: 0",
                                     font=('Segoe UI', 11, 'bold'))
        self.retry_label.grid(row=0, column=1, padx=20, pady=5)
        
        self.crowled_label = ttk.Label(stats_frame, text="Completados: 0",
                                       font=('Segoe UI', 11, 'bold'))
        self.crowled_label.grid(row=0, column=2, padx=20, pady=5)
        
        ttk.Button(stats_frame, text="🔄 Actualizar", command=self.update_stats).grid(
            row=0, column=3, padx=20, pady=5)
        
        # Frame de controles
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill="x", padx=15, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="▶ INICIAR CROW-LER", 
                                    command=self.start_crowler)
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ttk.Button(control_frame, text="⏸ DETENER", 
                                   command=self.stop_crowler, state="disabled")
        self.stop_btn.pack(side="left", padx=10)
        
        ttk.Button(control_frame, text="📁 ABRIR DATOS", 
                  command=self.open_data_folder).pack(side="left", padx=10)
        
        # Log de actividad
        log_frame = ttk.LabelFrame(self.root, text="📝 REGISTRO DE ACTIVIDAD", padding=10)
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=20, 
            state="disabled", 
            wrap="word",
            bg=Config.ENTRY_BG,
            fg=Config.FG_COLOR,
            font=('Consolas', 9),
            insertbackground=Config.FG_COLOR,
            selectbackground=Config.FG_COLOR,
            selectforeground=Config.BG_COLOR
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Barra de estado
        self.status_bar = tk.Label(
            self.root, 
            text="Listo - Crow-ler v2.0", 
            relief="sunken", 
            anchor="w",
            bg=Config.BG_SECONDARY,
            fg=Config.FG_COLOR,
            font=('Segoe UI', 9),
            padx=10,
            pady=5
        )
        self.status_bar.pack(fill="x", side="bottom")
    
    def log(self, message):
        """Agrega mensaje al log con colores"""
        self.log_text.config(state="normal")
        
        # Detectar tipo de mensaje para colorear
        if "✓" in message or "OK" in message or "exitosa" in message.lower():
            self.log_text.insert("end", f"{message}\n", "success")
            self.log_text.tag_config("success", foreground=Config.SUCCESS_COLOR)
        elif "✗" in message or "Error" in message or "error" in message.lower():
            self.log_text.insert("end", f"{message}\n", "error")
            self.log_text.tag_config("error", foreground=Config.ERROR_COLOR)
        elif "⚠" in message or "Advertencia" in message:
            self.log_text.insert("end", f"{message}\n", "warning")
            self.log_text.tag_config("warning", foreground=Config.WARNING_COLOR)
        else:
            self.log_text.insert("end", f"{message}\n")
        
        self.log_text.see("end")
        self.log_text.config(state="disabled")
    
    def check_requirements(self):
        """Verifica requisitos del sistema"""
        self.log("🔍 Verificando requisitos del sistema...")
        
        # Verificar Tor
        tor_path = AutoInstaller.check_tor_installed()
        if tor_path:
            self.tor_status.config(text="Tor: ✓ Instalado")
            self.log(f"✓ Tor encontrado en: {tor_path}")
        else:
            self.tor_status.config(text="Tor: ✗ No instalado")
            self.log("✗ Tor no encontrado")
        
        # Verificar PostgreSQL
        if AutoInstaller.check_postgresql_installed():
            self.db_status.config(text="PostgreSQL: ✓ Activo")
            self.log("✓ PostgreSQL conectado")
            
            # Crear DB y tablas
            try:
                DatabaseManager.create_database()
                DatabaseManager.init_tables()
                self.log("✓ Base de datos inicializada")
                self.update_stats()
            except Exception as e:
                self.log(f"✗ Error inicializando DB: {e}")
        else:
            self.db_status.config(text="PostgreSQL: ✗ No disponible")
            self.log("✗ PostgreSQL no disponible")
    
    def install_dependencies(self):
        """Instala dependencias automáticamente"""
        def install_thread():
            self.log("📥 Iniciando instalación automática...")
            
            # Crear directorios
            AutoInstaller.create_directories()
            self.log("✓ Directorios creados")
            
            # Instalar Tor (solo Windows)
            if platform.system() == "Windows":
                if not AutoInstaller.check_tor_installed():
                    self.log("📥 Instalando Tor...")
                    if AutoInstaller.install_tor_windows(self.log):
                        self.log("✓ Tor instalado")
                    else:
                        self.log("✗ Error instalando Tor")
                        self.log("⚠ Por favor descarga Tor manualmente desde:")
                        self.log("https://www.torproject.org/download/tor/")
            else:
                self.log("🐧 En Linux/Mac, instala Tor con:")
                self.log("  Ubuntu/Debian: sudo apt install tor")
                self.log("  Mac: brew install tor")
            
            # PostgreSQL requiere instalación manual
            if not AutoInstaller.check_postgresql_installed():
                self.log("\n⚠ PostgreSQL requiere instalación manual:")
                self.log("📥 Descarga desde: https://www.postgresql.org/download/")
                self.log("🔐 Durante la instalación, usa password: postgres")
            
            self.log("\n✓ Instalación completada. Verifica el estado.")
            self.root.after(100, self.check_requirements)
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def update_stats(self):
        """Actualiza las estadísticas"""
        try:
            q, r, c = DatabaseManager.get_stats()
            self.queue_label.config(text=f"Cola: {q}")
            self.retry_label.config(text=f"Reintentos: {r}")
            self.crowled_label.config(text=f"Completados: {c}")
        except Exception as e:
            self.log(f"✗ Error actualizando estadísticas: {e}")
    
    def start_crowler(self):
        """Inicia el crow-ler"""
        if self.crowler and self.crowler.running:
            self.log("⚠ El crow-ler ya está en ejecución")
            return
        
        # Actualizar semilla
        Config.SEED_URL = self.seed_entry.get()
        
        mode = self.mode_var.get()
        
        self.log(f"\n{'='*50}")
        self.log(f"🚀 Iniciando crow-ler en modo: {mode}")
        self.log(f"{'='*50}\n")
        
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_bar.config(text="🔄 Crow-ler en ejecución...")
        
        self.crowler = CrowlerEngine(gui_callback=self.log)
        self.crowler_thread = threading.Thread(
            target=self.crowler.crowl,
            args=(mode,),
            daemon=True
        )
        self.crowler_thread.start()
        
        # Actualizar estadísticas periódicamente
        self.update_stats_periodically()
    
    def update_stats_periodically(self):
        """Actualiza estadísticas cada 5 segundos"""
        if self.crowler and self.crowler.running:
            self.update_stats()
            self.root.after(5000, self.update_stats_periodically)
    
    def stop_crowler(self):
        """Detiene el crow-ler"""
        if self.crowler:
            self.log("\n⏸ Deteniendo crow-ler...")
            self.crowler.stop()
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.status_bar.config(text="⏸ Crow-ler detenido")
    
    def open_data_folder(self):
        """Abre la carpeta de datos"""
        path = Config.DATA_DIR
        
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])

# ============================================
# PUNTO DE ENTRADA
# ============================================

def main():
    """Función principal"""
    root = tk.Tk()
    app = CrowlerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()