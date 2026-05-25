## Paso 1 — Instalar las librerías de Python

Abre una terminal en VS Code:  
**Terminal → New Terminal**

Copia y pega este comando y presiona **Enter**:
pip install PyQT5 bleak

Espera a que termine — vas a ver mucho texto, eso es normal ✅

> ⚠️ Si ves un error que dice `pip no se reconoce`, prueba con:
> ```
> python -m pip install PyQt5 bleak
> ```

---

---

## Paso 2 — Cargar el programa al SPIKE

Picar en compilar e iniciar programa **`david_spike_hub.py`**

---

## Paso 3 — Correr la interfaz en tu computadora

1. Abre el archivo **`david_spike_gui.py`**
2. Córrelo con el botón **▷ Run Python File** (arriba a la derecha)  
3. Se abre la ventana del controlador

---

## Paso 4 — Conectar por Bluetooth

1. Asegúrate de que el **Bluetooth de tu computadora esté activado**
2. En la ventana del programa, haz clic en **🔵 Buscar y Conectar SPIKE**
3. El programa va a escanear automáticamente — espera unos segundos
4. Cuando encuentre el SPIKE verás en el log: `✅ Conectado por Bluetooth`

> ⚠️ Si no lo encuentra:
> - Verifica que el SPIKE tenga la **luz verde** (programa corriendo)
> - Asegúrate de que ningún otro dispositivo esté ya conectado al SPIKE
> - Cierra Pybricks en el navegador si lo dejaste abierto

---

## Paso 5 — ¡Controlar el robot!

| Acción | Botón en pantalla | Teclado |
|--------|-------------------|---------|
| Avanzar | ▲ Forward | `W` o `↑` |
| Retroceder | ▼ Backward | `S` o `↓` |
| Girar izquierda | ◀ Left | `A` o `←` |
| Girar derecha | ▶ Right | `D` o `→` |
| Frenar | ■ Stop | (soltar tecla) |
| Subir brazo | Arm ▲ | — |
| Bajar brazo | Arm ▼ | — |
| Resetear posición | Reset posición (0,0) | — |

- El **mapa** muestra el recorrido del robot desde el punto (0,0)
- Los **círculos de colores** abajo del mapa muestran lo que detectan los sensores
- Ajusta la **velocidad** con el slider antes de moverte

---

## Paso 6 — Guardar el registro (opcional)

Haz clic en **💾 Exportar log a CSV** para guardar un archivo con todos los movimientos, coordenadas y colores detectados. Se puede abrir en Excel.

---

## ❓ Problemas comunes

| Problema | Solución |
|----------|----------|
| El SPIKE no aparece al buscar | Verifica que tenga la luz verde y que Pybricks no esté abierto en el navegador |
| Error `ModuleNotFoundError` | Vuelve a correr `pip install PyQt5 bleak` en la terminal |
| El teclado no mueve el robot | Haz clic en la ventana del programa primero para activarla |
| Se desconecta solo | Acerca la computadora al SPIKE, el BLE tiene rango limitado |
| La luz del SPIKE es roja | La batería está baja, cárgalo |