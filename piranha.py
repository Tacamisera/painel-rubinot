import tkinter as tk
import sys

try:
    import winsound  # Apenas no Windows
    def beep(freq=1000, dur=200):
        winsound.Beep(freq, dur)
except ImportError:
    def beep(freq=1000, dur=200):
        print(f"[BEEP] {freq}Hz por {dur}ms")  # Fallback no console

class CountdownTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Overlay Countdown")

        # Overlay sem bordas, sempre no topo
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)

        # Posição inicial
        self.root.geometry("+1200+30")

        # Label do timer
        self.label = tk.Label(
            self.root,
            text="",
            font=("Arial", 32, "bold"),
            fg="lime",
            bg="black"
        )
        self.label.pack(padx=10, pady=10)

        # Eventos do mouse
        self.label.bind("<Button-1>", self.reset_timer)        # clique simples → reinicia
        self.label.bind("<Double-Button-1>", self.close)       # duplo clique → fecha
        self.label.bind("<ButtonPress-1>", self.start_move)    # botão esquerdo segurar → arrastar
        self.label.bind("<B1-Motion>", self.do_move)

        # Tempo total e estado
        self.duration = 1 * 60 + 59
        self.remaining = self.duration
        self.blinking = False
        self.blink_state = True

        self.update_timer()
        self.root.mainloop()

    def reset_timer(self, event=None):
        """Reinicia o contador."""
        self.remaining = self.duration
        self.label.config(fg="lime", bg="black")
        self.blinking = False

    def close(self, event=None):
        """Fecha a aplicação."""
        self.root.destroy()

    def start_move(self, event):
        """Marca posição inicial do arraste (botão esquerdo)."""
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        """Arrasta a janela pela tela."""
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def update_timer(self):
        """Atualiza o display e controla o tempo."""
        mins, secs = divmod(self.remaining, 60)
        self.label.config(text=f"{mins:02}:{secs:02}")

        # Eventos de tempo
        if self.remaining == 30:
            beep(1000, 300)
            self.label.config(fg="red")
        elif self.remaining == 15:
            beep(1200, 300)
            self.blinking = True
            self.start_blink()

        # Contagem regressiva
        if self.remaining > 0:
            self.remaining -= 1
        else:
            self.reset_timer()

        self.root.after(1000, self.update_timer)

    def start_blink(self):
        """Pisca o texto em vermelho até zerar."""
        if self.blinking:
            self.blink_state = not self.blink_state
            self.label.config(fg="red" if self.blink_state else "black")
            self.root.after(500, self.start_blink)

if __name__ == "__main__":
    CountdownTimer()