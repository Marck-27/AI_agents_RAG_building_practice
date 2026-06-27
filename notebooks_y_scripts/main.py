"""
Main - Orquestador de Agentes IA
================================
Punto de entrada centralizado para ejecutar cualquier agente.
"""

# ===========================================
# Se agrega el path raiz para poder importar los modulos de la carpeta "/tools"
# ===========================================
import sys
from pathlib import Path

# Path del archivo actual
#PATH_FILE = Path.cwd() # usar con "notebooks.ipynb"
PATH_FILE = Path(__file__).parent # usar con "scripts.py"
print(f"Path del archivo actual: {PATH_FILE}")

# ===========================================
# Se crea función que importa modlulos indicando la carpeta y nombre del modulo.py
# ===========================================
from importlib.util import spec_from_file_location, module_from_spec

def cargar_modulo(nombre_carpeta: str, nombre_archivo: str):
    """Carga un módulo Python desde una carpeta con guiones en el nombre."""
    ruta = PATH_FILE / nombre_carpeta / nombre_archivo
    spec = spec_from_file_location(nombre_archivo.replace(".py", ""), ruta)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def mostrar_menu():
    """Muestra el menú de agentes disponibles."""
    print("\n" + "=" * 60)
    print("🤖 ORQUESTADOR DE AGENTES IA - DataPath")
    print("=" * 60)
    print("\nAgentes disponibles:\n")
    print("  A. Agente Básico (sin memoria)")
    print("  B. Agente con memoria histórica de conversación (PostgreSQL)")
    print("  C. Agente con Base de Conocimiento (Memoria + RAG + Tool)")
    print("  D. Agente Completo (Memoria + RAG + Tools (Fecha y Acceso a Internet)")
    print("\n  0. Salir")
    print("-" * 60)


def main():
    """Función principal del orquestador."""
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nSelecciona un agente (A/B/C/D o 0): ").strip().upper()
            
            if opcion == "0":
                print("\n¡Hasta luego! 👋\n")
                sys.exit(0)
            
            elif opcion == "A":
                modulo = cargar_modulo("02_Agente_Basico", "agente_basico.py")
                modulo.main()
            
            elif opcion == "B":
                modulo = cargar_modulo(
                    "03_Agente_Basico_con_Memoria_Historica", 
                    "agente_basico_conversation_history.py"
                )
                modulo.main()
            
            elif opcion == "C":
                modulo = cargar_modulo(
                    "05_Agente_con_RAG_basico", 
                    "agente_basico_hc_base_de_conocimiento.py"
                )
                modulo.main()
            
            elif opcion == "D":
                modulo = cargar_modulo(
                    "06_Agente_con_RAG_multi_tools", 
                    "agente_basico_hc_bc_toolexterna.py"
                )
                modulo.main()
            
            else:
                print("\n❌ Opción no válida. Intenta de nuevo.\n")
        
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego! 👋\n")
            sys.exit(0)
        
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
