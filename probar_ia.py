import sys
import json

# Asegurar encoding UTF-8 en consola de Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.services.gemini_service import GeminiService

def main():
    print("=" * 65)
    print("       MOTOR DE BUSQUEDA INTELIGENTE - FichaAI (Gemini AI)")
    print("=" * 65)
    print("Puedes escribir:")
    print(" 1. Solo el nombre del celular (ej: 'Samsung Galaxy A55', 'iPhone 15 Pro')")
    print(" 2. O pegar un texto completo con especificaciones tecnicas.")
    print(" (Escribe 'salir' para terminar)\n")

    while True:
        try:
            entrada = input("\n[>] Ingresa el modelo o texto del celular: ").strip()
            if not entrada:
                continue
            if entrada.lower() in ['salir', 'exit', 'q']:
                print("\nHasta luego!")
                break

            print(f"\n[...] Buscando y estructurando ficha tecnica para: '{entrada}'...")
            
            resultado = GeminiService.extraer_ficha_desde_texto(entrada)
            
            print("\n" + "-" * 60)
            print("                FICHA TECNICA GENERADA")
            print("-" * 60)
            print(f"  Modelo:           {resultado.get('modelo')}")
            print(f"  Procesador:       {resultado.get('procesador')}")
            print(f"  Camara Principal: {resultado.get('camara_principal')}")
            print(f"  Almacenamiento:   {resultado.get('almacenamiento')}")
            print(f"  Precio Oficial:   ${resultado.get('precio_oficial')} {resultado.get('moneda')}")
            print("-" * 60)
            print("\n[JSON Crudo]:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\nSaliendo...")
            break
        except Exception as e:
            print(f"\n[ERROR] Ocurrio un problema: {e}")

if __name__ == '__main__':
    main()
