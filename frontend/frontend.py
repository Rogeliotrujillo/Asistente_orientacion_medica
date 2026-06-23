# frontend/frontend.py
import reflex as rx
import httpx
import datetime

class State(rx.State):
    pregunta: str = ""
    respuesta: str = ""
    fuentes: str = ""
    historial: list = []
    cargando: bool = False
    error: str = ""
    
    def set_pregunta(self, value: str):
        self.pregunta = value
    
    async def consultar(self):
        if not self.pregunta.strip():
            self.error = "⚠️ Escribe una pregunta."
            return
        
        self.cargando = True
        self.error = ""
        self.respuesta = ""
        self.fuentes = ""
        pregunta_actual = self.pregunta
        self.pregunta = ""
        yield
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "http://127.0.0.1:8005/consultar",
                    json={"pregunta": pregunta_actual}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.respuesta = data.get("respuesta", "Sin respuesta.")
                    self.fuentes = data.get("fuentes", "No hay fuentes disponibles")
                    
                    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    self.historial.insert(0, {
                        "pregunta": pregunta_actual,
                        "respuesta": self.respuesta,
                        "fuentes": self.fuentes,
                        "timestamp": now
                    })
                else:
                    self.error = f"Error HTTP: {response.status_code}"
        except httpx.ConnectError:
            self.error = "❌ No se pudo conectar al servidor."
        except Exception as e:
            self.error = f"❌ Error: {str(e)}"
        
        self.cargando = False
        yield
    
    def limpiar(self):
        self.historial = []
        self.respuesta = ""
        self.fuentes = ""
        self.error = ""
    
    @rx.var
    def historial_texto(self) -> str:
        if not self.historial:
            return "No hay consultas en el historial."
        texto = ""
        for i, entry in enumerate(self.historial, 1):
            texto += f"📌 {i}\n"
            texto += f"   📅 {entry.get('timestamp', '')}\n"
            texto += f"   ❓ {entry.get('pregunta', '')[:50]}"
            if len(entry.get('pregunta', '')) > 50:
                texto += "..."
            texto += "\n"
            texto += f"   📚 {entry.get('fuentes', 'No hay fuentes')[:40]}"
            if len(entry.get('fuentes', '')) > 40:
                texto += "..."
            texto += "\n"
            texto += "-" * 30 + "\n"
        return texto


def index():
    return rx.center(
        rx.vstack(
            # ==========================================
            # HEADER - COMPACTO
            # ==========================================
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "🏥 Asistente de Orientación Médica Universitaria",
                        size="5",
                        color="#e2e8f0",
                    ),
                    rx.text(
                        "Consulta libros médicos con tecnología avanzada",
                        size="1",
                        color="#94a3b8",
                    ),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.badge(
                    "Activo",
                    color_scheme="green",
                    variant="soft",
                    size="1",
                ),
                spacing="3",
                width="100%",
                align="center",
                padding_bottom="4px",
            ),
            
            # ==========================================
            # ADVERTENCIA - COMPACTA
            # ==========================================
            rx.hstack(
                rx.text("⚠️", font_size="14px"),
                rx.text(
                    "Información educativa. No sustituye consulta médica.",
                    font_weight="bold",
                    color="#fcd34d",
                    font_size="11px",
                ),
                rx.text(
                    "| Apoyo académico basado en libros de salud.",
                    color="#94a3b8",
                    font_size="10px",
                ),
                spacing="2",
                align="center",
                bg="#1a1a2e",
                border="1px solid #fcd34d",
                padding="4px 10px",
                border_radius="6px",
                width="100%",
            ),
            
            # ==========================================
            # INPUT - COMPACTO
            # ==========================================
            rx.hstack(
                rx.text_area(
                    placeholder="Escribe tu pregunta médica...",
                    value=State.pregunta,
                    on_change=State.set_pregunta,
                    rows="2",
                    width="100%",
                    padding="8px 12px",
                    font_size="13px",
                    border_radius="6px",
                    border="2px solid #334155",
                    bg="#0f0f1a",
                    color="#e2e8f0",
                    _focus={"border_color": "#3b82f6"},
                    _placeholder={"color": "#64748b"},
                ),
                rx.vstack(
                    rx.button(
                        rx.cond(
                            State.cargando,
                            rx.text("Consultando...", font_size="13px"),
                            rx.text("Consultar", font_size="13px"),
                        ),
                        on_click=State.consultar,
                        bg="#3b82f6",
                        color="white",
                        padding="6px 16px",
                        border_radius="6px",
                        font_weight="600",
                        _hover={"bg": "#2563eb", "cursor": "pointer"},
                        is_disabled=State.cargando,
                        width="100%",
                    ),
                    rx.button(
                        "Limpiar",
                        on_click=State.limpiar,
                        variant="outline",
                        padding="4px 16px",
                        border_radius="6px",
                        color="#94a3b8",
                        border="1px solid #334155",
                        font_size="12px",
                        _hover={"bg": "#1e293b", "cursor": "pointer"},
                        width="100%",
                    ),
                    spacing="1",
                    width="auto",
                ),
                spacing="3",
                width="100%",
                align="end",
            ),
            
            # ==========================================
            # ERROR
            # ==========================================
            rx.cond(
                State.error,
                rx.hstack(
                    rx.text("❌", font_size="14px"),
                    rx.text(State.error, color="#f87171", font_size="12px"),
                    spacing="2",
                    align="center",
                    bg="#1a0a0a",
                    border="1px solid #f87171",
                    padding="4px 10px",
                    border_radius="6px",
                    width="100%",
                ),
            ),
            
            # ==========================================
            # CONTENIDO PRINCIPAL (2 columnas)
            # ==========================================
            rx.grid(
                # ==========================================
                # COLUMNA IZQUIERDA - RESPUESTA
                # ==========================================
                rx.cond(
                    State.respuesta,
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("📋 Respuesta:", font_weight="bold", font_size="18px", color="#e2e8f0"),
                                rx.spacer(),
                                rx.button(
                                    rx.icon("copy", size=14),
                                    on_click=rx.set_clipboard(State.respuesta),
                                    variant="ghost",
                                    color="#94a3b8",
                                    padding="2px 8px",
                                ),
                                width="100%",
                            ),
                            rx.divider(margin="4px 0", border_color="#334155"),
                            rx.scroll_area(
                                rx.text(
                                    State.respuesta,
                                    white_space="pre-wrap",
                                    font_size="16px",
                                    color="#cbd5e1",
                                    line_height="1.8",
                                ),
                                height="calc(100vh - 340px)",
                                width="100%",
                            ),
                            spacing="3",
                            align="start",
                            width="100%",
                        ),
                        bg="#1a1a2e",
                        padding="1rem 1.25rem",
                        border_radius="10px",
                        border_left="4px solid #3b82f6",
                        box_shadow="0 2px 8px rgba(0,0,0,0.3)",
                        width="100%",
                        height="calc(100vh - 240px)",
                        overflow="hidden",
                    ),
                    # Placeholder cuando no hay respuesta
                    rx.box(
                        rx.vstack(
                            rx.icon("message-square", size=48, color="#334155"),
                            rx.text("La respuesta aparecerá aquí", size="3", color="#64748b", font_weight="500"),
                            rx.text("Escribe una pregunta y presiona 'Consultar'", size="2", color="#4a5568"),
                            spacing="3",
                            align="center",
                            width="100%",
                        ),
                        bg="#1a1a2e",
                        padding="1rem 1.25rem",
                        border_radius="10px",
                        border="2px dashed #334155",
                        width="100%",
                        height="calc(100vh - 240px)",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                ),
                
                # ==========================================
                # COLUMNA DERECHA - HISTORIAL + FUENTES
                # ==========================================
                rx.vstack(
                    # Historial
                    rx.cond(
                        State.historial,
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.text("📜 Historial", font_weight="bold", font_size="14px", color="#e2e8f0"),
                                    rx.spacer(),
                                    rx.button(
                                        "🗑️",
                                        on_click=State.limpiar,
                                        variant="outline",
                                        padding="2px 8px",
                                        border_radius="4px",
                                        color="#f87171",
                                        border="1px solid #f87171",
                                        bg="transparent",
                                        font_size="12px",
                                        _hover={"bg": "#1a0a0a", "cursor": "pointer"},
                                    ),
                                    width="100%",
                                ),
                                rx.divider(margin="4px 0", border_color="#334155"),
                                rx.scroll_area(
                                    rx.text(
                                        State.historial_texto,
                                        white_space="pre-wrap",
                                        font_size="12px",
                                        color="#94a3b8",
                                        bg="#0f0f1a",
                                        padding="8px 10px",
                                        border_radius="6px",
                                        width="100%",
                                    ),
                                    height="calc(50vh - 200px)",
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            bg="#1a1a2e",
                            padding="1rem",
                            border_radius="10px",
                            box_shadow="0 2px 8px rgba(0,0,0,0.3)",
                            width="100%",
                        ),
                        # Placeholder historial vacío
                        rx.box(
                            rx.vstack(
                                rx.icon("clock", size=24, color="#334155"),
                                rx.text("Historial", size="2", color="#64748b", font_weight="500"),
                                rx.text("Las consultas aparecerán aquí", size="1", color="#4a5568"),
                                spacing="2",
                                align="center",
                                width="100%",
                            ),
                            bg="#1a1a2e",
                            padding="0.75rem",
                            border_radius="10px",
                            border="2px dashed #334155",
                            width="100%",
                            height="calc(50vh - 200px)",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                    ),
                    
                    # ==========================================
                    # FUENTES DE LA BÚSQUEDA ACTUAL (DEBAJO DEL HISTORIAL)
                    # ==========================================
                    rx.cond(
                        State.fuentes,
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.text("📚 Fuentes actuales", font_weight="bold", font_size="13px", color="#e2e8f0"),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.divider(margin="4px 0", border_color="#334155"),
                                rx.scroll_area(
                                    rx.text(
                                        State.fuentes,
                                        white_space="pre-wrap",
                                        font_size="12px",
                                        color="#94a3b8",
                                        bg="#0f0f1a",
                                        padding="8px 10px",
                                        border_radius="6px",
                                        width="100%",
                                    ),
                                    height="calc(30vh - 80px)",
                                    width="100%",
                                ),
                                spacing="2",
                                align="start",
                                width="100%",
                            ),
                            bg="#1a1a2e",
                            padding="0.75rem 1rem",
                            border_radius="10px",
                            border="1px solid #3b82f6",
                            box_shadow="0 2px 8px rgba(0,0,0,0.3)",
                            width="100%",
                            flex="1",
                            overflow="hidden",
                        ),
                        # Placeholder cuando no hay fuentes
                        rx.box(
                            rx.vstack(
                                rx.icon("book", size=20, color="#334155"),
                                rx.text("Fuentes actuales", size="1", color="#64748b", font_weight="500"),
                                rx.text("Las fuentes aparecerán aquí", size="1", color="#4a5568"),
                                spacing="1",
                                align="center",
                                width="100%",
                            ),
                            bg="#1a1a2e",
                            padding="0.75rem",
                            border_radius="10px",
                            border="2px dashed #334155",
                            width="100%",
                            flex="1",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                    ),
                    
                    spacing="2",
                    width="100%",
                ),
                
                columns="2fr 1fr",
                gap="3",
                width="100%",
                height="calc(100vh - 240px)",
            ),
            
            spacing="2",
            width="100%",
            max_width="1200px",
            padding="0.5rem 1rem",
        ),
        padding="0.5rem",
        bg="#0a0a14",
        min_height="100vh",
        height="100vh",
        overflow="hidden",
    )


app = rx.App()
app.add_page(index, title="Asistente de Orientación Médica Universitaria")