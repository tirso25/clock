#!/usr/bin/env python3
"""
Clock App - Reloj digital para terminal con cronómetro y Pomodoro
Controles:
  1 - Modo Reloj
  2 - Modo Cronómetro
  3 - Modo Pomodoro
  Espacio - Iniciar/Pausar (Cronómetro/Pomodoro)
  r - Reiniciar (Cronómetro/Pomodoro)
  s - Configurar tiempos (Pomodoro)
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


def time_to_ascii(time_str: str) -> str:
    """Convierte una cadena de tiempo (HH:MM:SS) a ASCII art."""
    lines = ["", "", "", "", ""]
    for char in time_str:
        if char in ASCII_DIGITS:
            for i, line in enumerate(ASCII_DIGITS[char]):
                lines[i] += line + " "
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
    """
    
    BINDINGS = [
        Binding("1", "mode_clock", "Reloj"),
        Binding("2", "mode_stopwatch", "Cronómetro"),
        Binding("3", "mode_pomodoro", "Pomodoro"),
        Binding("space", "toggle_start", "Iniciar/Pausar"),
        Binding("r", "reset", "Reiniciar"),
        Binding("s", "settings", "Configurar"),
        Binding("q", "quit", "Salir"),
    ]
    
    TITLE = "🕐 Clock App"
    
    def __init__(self) -> None:
        super().__init__()
        self.mode = "clock"  # clock, stopwatch, pomodoro
        
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
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Horizontal(id="tabs-container")
            yield Static("", id="date-display")
            yield Container(id="clock-container")
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
        ]
        
        for mode_id, name in modes:
            tab = ModeTab(mode_id, name, id=f"tab-{mode_id}")
            await tabs_container.mount(tab)
            tab.active = (self.mode == mode_id)
    
    def update_display(self) -> None:
        """Actualiza el display según el modo actual."""
        if self.mode == "clock":
            self.update_clock()
        elif self.mode == "stopwatch":
            self.update_stopwatch()
        elif self.mode == "pomodoro":
            self.update_pomodoro()
    
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
            info_bar.update("1-3: Cambiar modo | q: Salir")
        elif self.mode == "stopwatch":
            info_bar.update("Espacio: Iniciar/Pausar | r: Reiniciar | 1-3: Cambiar modo | q: Salir")
        elif self.mode == "pomodoro":
            info_bar.update(f"Focus: {self.pomodoro_focus_time}min | Descanso: {self.pomodoro_break_time}min | Espacio: Iniciar/Pausar | r: Reiniciar | s: Config | q: Salir")
    
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
    
    # Acciones de control
    def action_toggle_start(self) -> None:
        """Inicia o pausa el cronómetro/pomodoro."""
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
    
    def action_reset(self) -> None:
        """Reinicia el cronómetro/pomodoro."""
        if self.mode == "stopwatch":
            self.stopwatch_running = False
            self.stopwatch_elapsed = timedelta()
            self.stopwatch_start_time = None
        
        elif self.mode == "pomodoro":
            self.pomodoro_running = False
            self.pomodoro_is_focus = True
            self.pomodoro_remaining = timedelta(minutes=self.pomodoro_focus_time)
            self.pomodoro_start_time = None
    
    def action_settings(self) -> None:
        """Abre la configuración del Pomodoro."""
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


def main():
    app = ClockApp()
    app.run()


if __name__ == "__main__":
    main()