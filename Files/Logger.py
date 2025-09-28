import os
from datetime import datetime
import numpy as np

class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        # Crear directorio de logs si no existe
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Crear archivo de log con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"snake_game_log_{timestamp}.txt")
        self.move_counter = 0
        
    def log_state(self, grid, position, apple_pos, move=None, additional_info=None):
        """
        Registra el estado actual del juego en el archivo de log
        """
        self.move_counter += 1
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Movimiento #{self.move_counter} - {datetime.now().strftime('%H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            
            # Registrar la posición actual de la serpiente
            f.write(f"Posición de la cabeza: {position}\n")
            if apple_pos is not None:
                f.write(f"Posición de la manzana: {apple_pos}\n")
            else:
                f.write("Manzana no visible\n")
            
            if move:
                f.write(f"Movimiento realizado: {move}\n")
                
            # Registrar información adicional si existe
            if additional_info:
                f.write("\nInformación adicional:\n")
                f.write(additional_info + "\n")
            
            # Registrar la matriz del juego
            f.write("\nMatriz del juego:\n")
            # Crear una representación visual de la matriz
            visual_matrix = []
            for row in grid:
                row_str = ""
                for cell in row:
                    if cell == 0:    # Espacio vacío
                        row_str += "⬜"
                    elif cell == 2:   # Cuerpo de la serpiente
                        row_str += "🟩"
                    elif cell == 9:   # Pared
                        row_str += "⬛"
                    elif cell == 1:   # Manzana (si se usa)
                        row_str += "🔴"
                visual_matrix.append(row_str)
            
            f.write("\n".join(visual_matrix))
            f.write("\n\nLeyenda:\n")
            f.write("⬜ - Espacio vacío\n")
            f.write("🟩 - Serpiente\n")
            f.write("⬛ - Pared\n")
            f.write("🔴 - Manzana\n")
            
    def log_error(self, error_msg):
        """
        Registra mensajes de error en el archivo de log
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'!'*50}\n")
            f.write(f"ERROR - {datetime.now().strftime('%H:%M:%S')}\n")
            f.write(f"{'!'*50}\n")
            f.write(f"{error_msg}\n")