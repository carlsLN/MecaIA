# Cómo ejecutar MecaIA paso a paso

Esta guía es para Windows con Visual Studio Code. En macOS o Linux los pasos son iguales; solo
cambia el comando para activar el entorno virtual (ver paso 4).

## 1. Instalar lo necesario (una sola vez)

1. **Python 3.10 o superior**: descárgalo desde https://www.python.org/downloads/. En el instalador,
   marca la casilla **"Add Python to PATH"** antes de presionar Install.
2. **Visual Studio Code**: https://code.visualstudio.com/
3. En VS Code, abre la pestaña de extensiones (Ctrl+Shift+X) e instala la extensión **Python** de
   Microsoft.

Para comprobar que Python quedó instalado, abre una terminal y escribe `python --version`. Debe
mostrar algo como `Python 3.12.x`.

## 2. Obtener el proyecto

Elige una opción:

- **Desde GitHub:** en la página del repositorio, botón verde **Code** → **Download ZIP**, o con Git:
  `git clone https://github.com/carlsLN/MecaIA.git`
- **Desde el archivo mecaia.zip:** clic derecho → **Extraer todo**.

## 3. Abrir la carpeta en VS Code

**Archivo → Abrir carpeta** y elige la carpeta del proyecto (la que contiene `main.py` y
`README.md`). Luego abre una terminal dentro de VS Code: **Terminal → Nueva terminal**.

## 4. Crear el entorno virtual e instalar dependencias (una sola vez)

En la terminal de VS Code:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS o Linux
pip install -r requirements.txt
```

Si al activar aparece un error de "ejecución de scripts deshabilitada" en PowerShell, ejecuta una
vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentar.

Cuando el entorno está activo, la terminal muestra `(.venv)` al comienzo de la línea.

## 5. Usar el agente

```bash
python main.py --demo --ver-plan
```

Aparece un chat en la terminal. Prueba con:

- `¿Qué aceite necesito para mi Kawasaki 400?` y luego responde `la ninja`
- `ya cambié el aceite a los 12.000 km`
- `cómo reviso la presión de los neumáticos`
- `mi moto no frena, ¿qué hago?`
- `qué aceite lleva un Yamaha R3`

Escribe `salir` para terminar. La línea `[plan]` muestra las decisiones que tomó el agente.

Para usar a Claude como modelo de lenguaje (requiere una API key con créditos):

```bash
set ANTHROPIC_API_KEY=tu_api_key          # Windows (cmd)
$env:ANTHROPIC_API_KEY="tu_api_key"       # Windows (PowerShell)
python main.py --usuario ana --ver-plan
```

Nunca escribas la API key dentro del código ni la subas a GitHub.

## 6. Ejecutar las pruebas

```bash
python -m pytest -v
```

Al final debe decir `46 passed`. El resultado de referencia está en
`evidencias/resultado_pruebas.txt`.

## 7. Borrar la memoria para empezar de cero

El agente guarda la memoria en dos archivos que se crean solos: `mecaia.db` (vehículos y
mantenciones) y `mecaia_conversaciones.db` (conversaciones). Bórralos para partir de cero.
