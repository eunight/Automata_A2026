# Integrantes: Ramón Belandria y Eugenia Ramirez
import sys

SIMBOLOS_CAJERO = {
    "t": "Insertar tarjeta",
    "p": "Ingresar PIN",
    "opc": "Seleccionar Consulta de Saldo",
    "opr": "Seleccionar Retiro de Dinero",
    "opk": "Seleccionar Cambio de Clave",
    "nk": "Ingresar NUEVA clave",
    "m": "Ingresar monto a retirar",
    "f": "Finalizar operación y retirar tarjeta"
}

class MealyMachine:
    def __init__(self, states: set, input_alphabet: set, output_alphabet: set, initial: str, terminals: set, transitions: dict):
        self.states = states
        self.states.add("invalidInputState")
        self.input_alphabet = input_alphabet
        self.output_alphabet = output_alphabet
        self.CurrentState = initial
        self.terminals = terminals
        self.transitions = transitions

    def transition(self, input_symbol):
        if input_symbol not in self.input_alphabet:
            self.CurrentState = "invalidInputState"
            return "Error: Símbolo desconocido"

        state_transitions = self.transitions.get(self.CurrentState, {})
        transition_result = state_transitions.get(input_symbol)
        
        if transition_result:
            self.CurrentState = transition_result["next_state"]
            return transition_result["output_msg"]
        else:
            self.CurrentState = "invalidInputState"
            return "Error: Transición no definida"

class ComposedSystem:
    def __init__(self, cajero_file, banco_file):
        self.cajero = load_automaton(cajero_file)
        self.banco = load_automaton(banco_file)
        self.forzar_error_banco = False

    def ejecutar_simulacion(self):
        print("\n=== SISTEMA COMPUESTO: CAJERO & BANCO INTEROPERABLES ===")
        print(f"Estado Inicial Cajero: {self.cajero.CurrentState} | Estado Inicial Banco: {self.banco.CurrentState}")

        while self.cajero.CurrentState != "invalidInputState":
            print(f"\n--- MENÚ DEL USUARIO (Estado Actual: {self.cajero.CurrentState}) ---")
            opciones_validas = self.cajero.transitions.get(self.cajero.CurrentState, {})
            
            entradas_usuario = [opt for opt in opciones_validas.keys() if opt in SIMBOLOS_CAJERO]
            
            for opt in entradas_usuario:
                print(f"  [{opt}] -> {SIMBOLOS_CAJERO[opt]}")
            print("  [error] -> Alternar estado del Banco (Simular caídas/fallos de saldo)")
            print("  [exit]  -> Salir de la aplicación")
            print(f"  * Estado del Servidor Banco: {'MODO CONFIGURADO PARA SIMULAR RECHAZOS' if self.forzar_error_banco else 'MODO NORMAL (OPERACIONES EXITOSAS)'}")
            print("-" * 60)

            entry = input("Seleccione acción: ").strip().lower()

            if entry == "exit":
                break
            if entry == "error":
                self.forzar_error_banco = not self.forzar_error_banco
                print(f"\n[!] Estado del banco modificado.")
                continue
            if entry not in entradas_usuario:
                print(f"\n[!] Entrada inválida para el estado actual del cajero.")
                continue

            print(f"\n[+] Acción ejecutada: {SIMBOLOS_CAJERO[entry]}")
            msg_salida_cajero = self.cajero.transition(entry)
            print(f" -> Cajero cambia a estado: {self.cajero.CurrentState}")
            print(f" -> Mensaje enviado por la red: [{msg_salida_cajero}]")

            if msg_salida_cajero in self.banco.input_alphabet:
                print(f"\n[Red] Transmitiendo [{msg_salida_cajero}] al Servidor del Banco...")
                
                msg_respuesta_banco = self.banco.transition(msg_salida_cajero)
                
                if self.forzar_error_banco:
                    if msg_respuesta_banco == "vok": msg_respuesta_banco = "verr"
                    elif msg_respuesta_banco == "sok": msg_respuesta_banco = "serr"

                print(f" -> Banco procesa en estado interno: {self.banco.CurrentState}")
                print(f" -> Respuesta generada por el Banco: [{msg_respuesta_banco}]")
                
                self.banco.CurrentState = "b_reposo"

                msg_final_cajero = self.cajero.transition(msg_respuesta_banco)
                print(f"\n[Red] Cajero recibe respuesta [{msg_respuesta_banco}]")
                print(f" -> Estado Final del Cajero: {self.cajero.CurrentState}")
                print(f" -> Acción de Actuadores locales: [{msg_final_cajero}]")

            if self.cajero.CurrentState in self.cajero.terminals:
                print(f"\n[*] Ciclo finalizado en estado terminal: {self.cajero.CurrentState}")
                if self.cajero.CurrentState == "q_blok":
                    print("[!] TARJETA RETENIDA POR MEDIDA DE SEGURIDAD.")
                print("--- Reiniciando componentes para el siguiente ciclo ---")
                self.cajero.CurrentState = "q0"
                self.banco.CurrentState = "b_reposo"

def load_transition(transitions: dict, line: str):
    splittedLine = line.split(',')
    if len(splittedLine) != 4: return
    transitions.setdefault(splittedLine[0], {})[splittedLine[1]] = {
        "next_state": splittedLine[2], "output_msg": splittedLine[3]
    }

def load_automaton(filename: str) -> MealyMachine:
    try:
        with open(filename, 'r') as file: lines = file.readlines()
    except FileNotFoundError: sys.exit(f"Error: Archivo {filename} ausente.")
    states, input_alphabet, output_alphabet, terminals = set(), set(), set(), set()
    initial, transitions, entry_mode = "", dict(), " "
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            if line.startswith('#'): entry_mode = line
            continue
        match entry_mode:
            case "#estados": states = set(line.split(','))
            case "#alfabeto_entrada": input_alphabet = set(line.split(','))
            case "#alfabeto_salida": output_alphabet = set(line.split(','))
            case "#inicial": initial = line
            case "#terminales": terminals = set(line.split(','))
            case "#transiciones": load_transition(transitions, line)
    return MealyMachine(states, input_alphabet, output_alphabet, initial, terminals, transitions)

if __name__ == "__main__":
    sistema = ComposedSystem("automata_cajero.txt", "automata_banco.txt")
    sistema.ejecutar_simulacion()