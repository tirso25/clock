#!/usr/bin/env python3
"""
Clock App - Reloj digital para terminal con cronómetro, Pomodoro, Temporizador y Calendario
Controles:
  1 - Modo Reloj
  2 - Modo Cronómetro
  3 - Modo Pomodoro
  4 - Modo Temporizador
  5 - Modo Calendario
  Espacio - Iniciar/Pausar (Cronómetro/Pomodoro/Temporizador)
  r - Reiniciar (Cronómetro/Pomodoro/Temporizador)
  s - Configurar tiempos (Pomodoro/Temporizador)
  ←/→ - Mes anterior/siguiente (Calendario)
  t - Ir a hoy (Calendario)
  q - Salir
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual.binding import Binding
from textual import on
from typing import Optional
from datetime import datetime, timedelta
import calendar
import asyncio


# Dígitos ASCII art (altura 5)
ASCII_DIGITS = {
    '0': [
        "█████",
        "█   █",
        "█   █",
        "█   █",
        "█████",
    ],
    '1': [
        "  █  ",
        " ██  ",
        "  █  ",
        "  █  ",
        "█████",
    ],
    '2': [
        "█████",
        "    █",
        "█████",
        "█    ",
        "█████",
    ],
    '3': [
        "█████",
        "    █",
        "█████",
        "    █",
        "█████",
    ],
    '4': [
        "█   █",
        "█   █",
        "█████",
        "    █",
        "    █",
    ],
    '5': [
        "█████",
        "█    ",
        "█████",
        "    █",
        "█████",
    ],
    '6': [
        "█████",
        "█    ",
        "█████",
        "█   █",
        "█████",
    ],
    '7': [
        "█████",
        "    █",
        "   █ ",
        "  █  ",
        "  █  ",
    ],
    '8': [
        "█████",
        "█   █",
        "█████",
        "█   █",
        "█████",
    ],
    '9': [
        "█████",
        "█   █",
        "█████",
        "    █",
        "█████",
    ],
    ':': [
        "     ",
        "  █  ",
        "     ",
        "  █  ",
        "     ",
    ],
}

# Nombres de meses en español
MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Días de la semana en español (abreviados)
DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]


def time_to_ascii(time_str: str) -> str:
    """Convierte una cadena de tiempo (HH:MM:SS) a ASCII art."""
    lines = ["", "", "", "", ""]
    for char in time_str:
        if char in ASCII_DIGITS:
            for i, line in enumerate(ASCII_DIGITS[char]):
                lines[i] += line + " "
    return "\n".join(lines)


def generate_calendar(year: int, month: int, today: datetime) -> str:
    """Genera un calendario mensual en formato texto."""
    cal = calendar.Calendar(firstweekday=0)  # Lunes = 0
    
    # Cabecera con mes y año
    header = f"         {MESES[month]} {year}         "
    
    # Días de la semana
    days_header = "  ".join(DIAS_SEMANA)
    
    # Generar las semanas
    weeks = []
    for week in cal.monthdayscalendar(year, month):
        week_str = ""
        for i, day in enumerate(week):
            if day == 0:
                week_str += "    "
            else:
                # Resaltar el día actual
                if year == today.year and month == today.month and day == today.day:
                    week_str += f"[bold cyan][{day:2d}][/bold cyan]"
                else:
                    week_str += f" {day:2d} "
        weeks.append(week_str)
    
    # Construir calendario completo
    lines = [
        "",
        header,
        "─" * len(header),
        days_header,
        "─" * len(days_header),
    ]
    lines.extend(weeks)
    
    return "\n".join(lines)


class ConfigModal(ModalScreen[Optional[tuple[int, int]]]):
    """Modal para configurar tiempos del Pomodoro."""
    
    DEFAULT_CSS = """
    ConfigModal {
        align: center middle;
    }
    
    ConfigModal > Container {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    
    ConfigModal .modal-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }
    
    ConfigModal .input-label {
        margin-top: 1;
    }
    
    ConfigModal Input {
        width: 100%;
        margin-bottom: 1;
    }
    
    ConfigModal .button-row {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    ConfigModal Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancelar", show=False),
    ]
    
    def __init__(self, focus_time: int, break_time: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.focus_time = focus_time
        self.break_time = break_time
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("⚙️  Configurar Pomodoro", classes="modal-title")
            yield Label("Tiempo de focus (minutos):", classes="input-label")
            yield Input(value=str(self.focus_time), id="focus-input", type="integer")
            yield Label("Tiempo de descanso (minutos):", classes="input-label")
            yield Input(value=str(self.break_time), id="break-input", type="integer")
            with Horizontal(classes="button-row"):
                yield Button("Guardar", variant="primary", id="save")
                yield Button("Cancelar", variant="default", id="cancel")
    
    def on_mount(self) -> None:
        self.query_one("#focus-input", Input).focus()
    
    @on(Button.Pressed, "#save")
    def on_save(self) -> None:
        try:
            focus = int(self.query_one("#focus-input", Input).value)
            break_t = int(self.query_one("#break-input", Input).value)
            if focus > 0 and break_t > 0:
                self.dismiss((focus, break_t))
            else:
                self.dismiss(None)
        except ValueError:
            self.dismiss(None)
    
    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)
    
    def action_cancel(self) -> None:
        self.dismiss(None)

class TimerConfigModal(ModalScreen[Optional[tuple[int, int, str]]]):
    """Modal para configurar el temporizador."""
    
    DEFAULT_CSS = """
    TimerConfigModal {
        align: center middle;
    }
    
    TimerConfigModal > Container {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    
    TimerConfigModal .modal-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }
    
    TimerConfigModal .input-label {
        margin-top: 1;
    }
    
    TimerConfigModal Input {
        width: 100%;
        margin-bottom: 1;
    }
    
    TimerConfigModal .button-row {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    TimerConfigModal Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancelar", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("⏲️  Configurar Temporizador", classes="modal-title")
            yield Label("Minutos:", classes="input-label")
            yield Input(value="5", id="minutes-input", type="integer", placeholder="Minutos")
            yield Label("Segundos:", classes="input-label")
            yield Input(value="0", id="seconds-input", type="integer", placeholder="Segundos")
            yield Label("Nombre (opcional):", classes="input-label")
            yield Input(value="", id="name-input", placeholder="Ej: Café, Reunión...")
            with Horizontal(classes="button-row"):
                yield Button("Iniciar", variant="primary", id="start")
                yield Button("Cancelar", variant="default", id="cancel")
    
    def on_mount(self) -> None:
        self.query_one("#minutes-input", Input).focus()
    
    @on(Button.Pressed, "#start")
    def on_start(self) -> None:
        try:
            minutes = int(self.query_one("#minutes-input", Input).value or "0")
            seconds = int(self.query_one("#seconds-input", Input).value or "0")
            name = self.query_one("#name-input", Input).value.strip()
            
            if minutes > 0 or seconds > 0:
                self.dismiss((minutes, seconds, name))
            else:
                self.dismiss(None)
        except ValueError:
            self.dismiss(None)
    
    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)
    
    def action_cancel(self) -> None:
        self.dismiss(None)

class ClockDisplay(Static):
    """Widget para mostrar el reloj en ASCII."""
    
    DEFAULT_CSS = """
    ClockDisplay {
        width: 100%;
        height: auto;
        content-align: center middle;
        text-align: center;
        padding: 2;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.time_str = "00:00:00"
    
    def update_time(self, time_str: str) -> None:
        self.time_str = time_str
        self.update(time_to_ascii(time_str))


class CalendarDisplay(Static):
    """Widget para mostrar el calendario."""
    
    DEFAULT_CSS = """
    CalendarDisplay {
        width: 100%;
        height: auto;
        content-align: center middle;
        text-align: center;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
    
    def update_calendar(self) -> None:
        today = datetime.now()
        cal_text = generate_calendar(self.current_year, self.current_month, today)
        self.update(cal_text)
    
    def next_month(self) -> None:
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar()
    
    def prev_month(self) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar()
    
    def go_to_today(self) -> None:
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        self.update_calendar()


class ModeTab(Static):
    """Widget para una pestaña de modo."""
    
    DEFAULT_CSS = """
    ModeTab {
        width: auto;
        height: 3;
        padding: 0 3;
        margin: 0 1;
        border: solid $primary-background;
        content-align: center middle;
    }
    
    ModeTab:hover {
        background: $boost;
    }
    
    ModeTab.active {
        border: solid $accent;
        background: $accent 20%;
        text-style: bold;
    }
    """
    
    def __init__(self, mode_id: str, name: str, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.mode_id = mode_id
        self._active = False
    
    @property
    def active(self) -> bool:
        return self._active
    
    @active.setter
    def active(self, value: bool) -> None:
        self._active = value
        if value:
            self.add_class("active")
        else:
            self.remove_class("active")


class ClockApp(App):
    """Aplicación de reloj para terminal."""
    
    CSS = """
    Screen {
        background: $background;
    }
    
    #main-container {
        width: 100%;
        height: 1fr;
        align: center middle;
    }
    
    #tabs-container {
        width: 100%;
        height: 3;
        align: center middle;
        dock: top;
        padding: 1;
    }
    
    #clock-container {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 2;
    }
    
    #calendar-container {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
        display: none;
    }
    
    #calendar-container.visible {
        display: block;
    }
    
    #status {
        width: 100%;
        height: auto;
        text-align: center;
        padding: 1;
        color: $text-muted;
    }
    
    #date-display {
        width: 100%;
        height: auto;
        text-align: center;
        padding: 1;
        color: $text;
        text-style: bold;
    }
    
    #pomodoro-status {
        width: 100%;
        height: auto;
        text-align: center;
        padding: 1;
    }
    
    .focus-mode {
        color: $success;
    }
    
    .break-mode {
        color: $warning;
    }
    
    #info-bar {
        dock: bottom;
        width: 100%;
        height: 1;
        background: $primary-background;
        color: $text;
        padding: 0 2;
    }
    
    #calendar-nav {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
    }
    
    #calendar-nav Button {
        margin: 0 2;
    }
    """
    
    BINDINGS = [
        Binding("1", "mode_clock", "Reloj"),
        Binding("2", "mode_stopwatch", "Cronómetro"),
        Binding("3", "mode_pomodoro", "Pomodoro"),
        Binding("4", "mode_timer", "Temporizador"),  # CAMBIADO
        Binding("5", "mode_calendar", "Calendario"),  # CAMBIADO
        Binding("space", "toggle_start", "Iniciar/Pausar"),
        Binding("r", "reset", "Reiniciar"),
        Binding("s", "settings", "Configurar"),
        Binding("left", "prev_month", "Mes anterior", show=False),
        Binding("right", "next_month", "Mes siguiente", show=False),
        Binding("t", "go_today", "Ir a hoy", show=False),
        Binding("q", "quit", "Salir"),
    ]
    
    TITLE = "🕐 Clock App"
    theme = "dracula"
    
    def __init__(self) -> None:
        super().__init__()
        self.mode = "clock"  # clock, stopwatch, pomodoro, calendar, timer
        
        # Cronómetro
        self.stopwatch_running = False
        self.stopwatch_elapsed = timedelta()
        self.stopwatch_start_time: Optional[datetime] = None
        
        # Pomodoro
        self.pomodoro_running = False
        self.pomodoro_focus_time = 25  # minutos
        self.pomodoro_break_time = 5   # minutos
        self.pomodoro_remaining = timedelta(minutes=25)
        self.pomodoro_is_focus = True  # True = focus, False = break
        self.pomodoro_start_time: Optional[datetime] = None
        self.pomodoro_paused_remaining: Optional[timedelta] = None
        
        # Temporizador (NUEVO)
        self.timer_running = False
        self.timer_duration = timedelta()
        self.timer_remaining = timedelta()
        self.timer_start_time: Optional[datetime] = None
        self.timer_name = ""
        self.timer_finished = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Horizontal(id="tabs-container")
            yield Static("", id="date-display")
            yield Container(id="clock-container")
            yield Container(id="calendar-container")
            yield Static("", id="status")
            yield Static("", id="pomodoro-status")
        yield Static("", id="info-bar")
        yield Footer()
    
    async def on_mount(self) -> None:
        await self.refresh_tabs()
        
        # Crear el display del reloj
        clock_container = self.query_one("#clock-container", Container)
        self.clock_display = ClockDisplay(id="clock-display")
        await clock_container.mount(self.clock_display)
        
        # Crear el display del calendario
        calendar_container = self.query_one("#calendar-container", Container)
        self.calendar_display = CalendarDisplay(id="calendar-display")
        await calendar_container.mount(self.calendar_display)
        
        # Iniciar el timer de actualización
        self.set_interval(0.1, self.update_display)
        
        self.update_info_bar()
    
    async def refresh_tabs(self) -> None:
        """Refresca las pestañas de modos."""
        tabs_container = self.query_one("#tabs-container", Horizontal)
        await tabs_container.remove_children()
        
        modes = [
            ("clock", "🕐 Reloj"),
            ("stopwatch", "⏱️  Cronómetro"),
            ("pomodoro", "🍅 Pomodoro"),
            ("timer", "⏲️  Temporizador"),  # NUEVO
            ("calendar", "📅 Calendario"),
        ]
        
        for mode_id, name in modes:
            tab = ModeTab(mode_id, name, id=f"tab-{mode_id}")
            await tabs_container.mount(tab)
            tab.active = (self.mode == mode_id)
    
    def update_display(self) -> None:
        """Actualiza el display según el modo actual."""
        # Mostrar/ocultar contenedores según el modo
        clock_container = self.query_one("#clock-container", Container)
        calendar_container = self.query_one("#calendar-container", Container)
        
        if self.mode == "calendar":
            clock_container.styles.display = "none"
            calendar_container.add_class("visible")
            calendar_container.styles.display = "block"
        else:
            clock_container.styles.display = "block"
            calendar_container.remove_class("visible")
            calendar_container.styles.display = "none"
        
        if self.mode == "clock":
            self.update_clock()
        elif self.mode == "stopwatch":
            self.update_stopwatch()
        elif self.mode == "pomodoro":
            self.update_pomodoro()
        elif self.mode == "timer":  # NUEVO
            self.update_timer()
        elif self.mode == "calendar":
            self.update_calendar_view()
    
    def update_timer(self) -> None:
        """Actualiza el temporizador."""
        if self.timer_running and self.timer_start_time:
            elapsed = datetime.now() - self.timer_start_time
            remaining = self.timer_remaining - elapsed
            
            if remaining.total_seconds() <= 0:
                # Temporizador terminado
                remaining = timedelta()
                self.timer_running = False
                if not self.timer_finished:
                    self.timer_finished = True
                    title = self.timer_name if self.timer_name else "Temporizador"
                    self.notify("⏰ ¡Tiempo terminado!", title=title, timeout=10)
        else:
            remaining = self.timer_remaining
        
        # Asegurar que no sea negativo
        if remaining.total_seconds() < 0:
            remaining = timedelta()
        
        # Formatear tiempo
        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.clock_display.update_time(time_str)
        
        # Actualizar status
        date_display = self.query_one("#date-display", Static)
        if self.timer_name:
            date_display.update(f"⏲️  {self.timer_name}")
        else:
            date_display.update("⏲️  Temporizador")
        
        status = self.query_one("#status", Static)
        if self.timer_finished:
            status.update("🔔 ¡TERMINADO!")
        elif self.timer_running:
            status.update("▶️  En marcha")
        elif self.timer_duration.total_seconds() > 0:
            status.update("⏸️  Pausado")
        else:
            status.update("Pulsa 's' para configurar")
        
        pomodoro_status = self.query_one("#pomodoro-status", Static)
        pomodoro_status.update("")
    
    def update_clock(self) -> None:
        """Actualiza el reloj."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.clock_display.update_time(time_str)
        
        # Actualizar fecha
        date_str = now.strftime("%A, %d de %B de %Y")
        date_display = self.query_one("#date-display", Static)
        date_display.update(f"📅 {date_str}")
        
        # Limpiar status
        status = self.query_one("#status", Static)
        status.update("")
        
        pomodoro_status = self.query_one("#pomodoro-status", Static)
        pomodoro_status.update("")
    
    def update_stopwatch(self) -> None:
        """Actualiza el cronómetro."""
        if self.stopwatch_running and self.stopwatch_start_time:
            elapsed = self.stopwatch_elapsed + (datetime.now() - self.stopwatch_start_time)
        else:
            elapsed = self.stopwatch_elapsed
        
        # Formatear tiempo
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.clock_display.update_time(time_str)
        
        # Actualizar status
        date_display = self.query_one("#date-display", Static)
        date_display.update("⏱️  Cronómetro")
        
        status = self.query_one("#status", Static)
        if self.stopwatch_running:
            status.update("▶️  En marcha")
        else:
            status.update("⏸️  Pausado")
        
        pomodoro_status = self.query_one("#pomodoro-status", Static)
        pomodoro_status.update("")
    
    def update_pomodoro(self) -> None:
        """Actualiza el Pomodoro."""
        if self.pomodoro_running and self.pomodoro_start_time:
            elapsed = datetime.now() - self.pomodoro_start_time
            remaining = self.pomodoro_remaining - elapsed
            
            if remaining.total_seconds() <= 0:
                # Cambiar de modo
                self.pomodoro_is_focus = not self.pomodoro_is_focus
                if self.pomodoro_is_focus:
                    self.pomodoro_remaining = timedelta(minutes=self.pomodoro_focus_time)
                else:
                    self.pomodoro_remaining = timedelta(minutes=self.pomodoro_break_time)
                self.pomodoro_start_time = datetime.now()
                self.notify_pomodoro_change()
                remaining = self.pomodoro_remaining
        else:
            remaining = self.pomodoro_remaining
        
        # Asegurar que no sea negativo
        if remaining.total_seconds() < 0:
            remaining = timedelta()
        
        # Formatear tiempo
        total_seconds = int(remaining.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        time_str = f"00:{minutes:02d}:{seconds:02d}"
        self.clock_display.update_time(time_str)
        
        # Actualizar status
        date_display = self.query_one("#date-display", Static)
        date_display.update("🍅 Pomodoro")
        
        status = self.query_one("#status", Static)
        if self.pomodoro_running:
            status.update("▶️  En marcha")
        else:
            status.update("⏸️  Pausado")
        
        pomodoro_status = self.query_one("#pomodoro-status", Static)
        if self.pomodoro_is_focus:
            pomodoro_status.update("[bold green]🎯 FOCUS[/bold green]")
        else:
            pomodoro_status.update("[bold yellow]☕ DESCANSO[/bold yellow]")
    
    def update_calendar_view(self) -> None:
        """Actualiza la vista del calendario."""
        self.calendar_display.update_calendar()
        
        # Actualizar cabecera
        date_display = self.query_one("#date-display", Static)
        date_display.update("📅 Calendario")
        
        # Mostrar navegación en status
        status = self.query_one("#status", Static)
        status.update("← → Navegar meses | t Ir a hoy")
        
        pomodoro_status = self.query_one("#pomodoro-status", Static)
        pomodoro_status.update("")
    
    def notify_pomodoro_change(self) -> None:
        """Notifica el cambio de modo en Pomodoro."""
        if self.pomodoro_is_focus:
            self.notify("🎯 ¡Tiempo de focus!", title="Pomodoro")
        else:
            self.notify("☕ ¡Tiempo de descanso!", title="Pomodoro")
    
    def update_info_bar(self) -> None:
        """Actualiza la barra de información."""
        info_bar = self.query_one("#info-bar", Static)
        
        if self.mode == "clock":
            info_bar.update("1-5: Cambiar modo | q: Salir")
        elif self.mode == "stopwatch":
            info_bar.update("Espacio: Iniciar/Pausar | r: Reiniciar | 1-5: Cambiar modo | q: Salir")
        elif self.mode == "pomodoro":
            info_bar.update(f"Focus: {self.pomodoro_focus_time}min | Descanso: {self.pomodoro_break_time}min | Espacio: Iniciar/Pausar | r: Reiniciar | s: Config | q: Salir")
        elif self.mode == "timer":
            info_bar.update("s: Configurar | Espacio: Iniciar/Pausar | r: Reiniciar | 1-5: Cambiar modo | q: Salir")
        elif self.mode == "calendar":
            info_bar.update("←/→: Cambiar mes | t: Ir a hoy | 1-5: Cambiar modo | q: Salir")
        
    # Acciones de modo
    async def action_mode_clock(self) -> None:
        """Cambia al modo reloj."""
        self.mode = "clock"
        await self.refresh_tabs()
        self.update_info_bar()
    
    async def action_mode_stopwatch(self) -> None:
        """Cambia al modo cronómetro."""
        self.mode = "stopwatch"
        await self.refresh_tabs()
        self.update_info_bar()
    
    async def action_mode_pomodoro(self) -> None:
        """Cambia al modo pomodoro."""
        self.mode = "pomodoro"
        await self.refresh_tabs()
        self.update_info_bar()
    
    async def action_mode_calendar(self) -> None:
        """Cambia al modo calendario."""
        self.mode = "calendar"
        await self.refresh_tabs()
        self.update_info_bar()
    
    async def action_mode_timer(self) -> None:
        """Cambia al modo temporizador."""
        self.mode = "timer"
        await self.refresh_tabs()
        self.update_info_bar()
    
    # Acciones de control
    def action_toggle_start(self) -> None:
        """Inicia o pausa el cronómetro/pomodoro/temporizador."""
        if self.mode == "stopwatch":
            if self.stopwatch_running:
                # Pausar
                self.stopwatch_elapsed += datetime.now() - self.stopwatch_start_time
                self.stopwatch_start_time = None
                self.stopwatch_running = False
            else:
                # Iniciar
                self.stopwatch_start_time = datetime.now()
                self.stopwatch_running = True
        
        elif self.mode == "pomodoro":
            if self.pomodoro_running:
                # Pausar
                if self.pomodoro_start_time:
                    elapsed = datetime.now() - self.pomodoro_start_time
                    self.pomodoro_remaining -= elapsed
                self.pomodoro_start_time = None
                self.pomodoro_running = False
            else:
                # Iniciar
                self.pomodoro_start_time = datetime.now()
                self.pomodoro_running = True
        
        elif self.mode == "timer":  # NUEVO
            if self.timer_duration.total_seconds() == 0:
                # No hay temporizador configurado, abrir config
                self.action_settings()
            elif self.timer_running:
                # Pausar
                if self.timer_start_time:
                    elapsed = datetime.now() - self.timer_start_time
                    self.timer_remaining -= elapsed
                self.timer_start_time = None
                self.timer_running = False
            else:
                # Iniciar
                self.timer_start_time = datetime.now()
                self.timer_running = True
                self.timer_finished = False
    
    def action_reset(self) -> None:
        """Reinicia el cronómetro/pomodoro/temporizador."""
        if self.mode == "stopwatch":
            self.stopwatch_running = False
            self.stopwatch_elapsed = timedelta()
            self.stopwatch_start_time = None
        
        elif self.mode == "pomodoro":
            self.pomodoro_running = False
            self.pomodoro_is_focus = True
            self.pomodoro_remaining = timedelta(minutes=self.pomodoro_focus_time)
            self.pomodoro_start_time = None
        
        elif self.mode == "timer":  # NUEVO
            self.timer_running = False
            self.timer_remaining = self.timer_duration
            self.timer_start_time = None
            self.timer_finished = False
    
    def action_settings(self) -> None:
        """Abre la configuración del Pomodoro o Temporizador."""
        if self.mode == "pomodoro":
            def on_result(result: Optional[tuple[int, int]]) -> None:
                if result:
                    focus, break_t = result
                    self.pomodoro_focus_time = focus
                    self.pomodoro_break_time = break_t
                    # Reiniciar con nuevos tiempos
                    self.pomodoro_running = False
                    self.pomodoro_is_focus = True
                    self.pomodoro_remaining = timedelta(minutes=self.pomodoro_focus_time)
                    self.pomodoro_start_time = None
                    self.update_info_bar()
            
            self.push_screen(
                ConfigModal(self.pomodoro_focus_time, self.pomodoro_break_time),
                on_result
            )
        
        elif self.mode == "timer":  # NUEVO
            def on_result(result: Optional[tuple[int, int, str]]) -> None:
                if result:
                    minutes, seconds, name = result
                    self.timer_duration = timedelta(minutes=minutes, seconds=seconds)
                    self.timer_remaining = self.timer_duration
                    self.timer_name = name
                    self.timer_running = False
                    self.timer_start_time = None
                    self.timer_finished = False
            
            self.push_screen(TimerConfigModal(), on_result)
    
    # Acciones de calendario
    def action_prev_month(self) -> None:
        """Ir al mes anterior."""
        if self.mode == "calendar":
            self.calendar_display.prev_month()
    
    def action_next_month(self) -> None:
        """Ir al mes siguiente."""
        if self.mode == "calendar":
            self.calendar_display.next_month()
    
    def action_go_today(self) -> None:
        """Ir al mes actual."""
        if self.mode == "calendar":
            self.calendar_display.go_to_today()


def main():
    app = ClockApp()
    app.run()


if __name__ == "__main__":
    main()
