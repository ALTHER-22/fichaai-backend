import sys
import json

# Asegurar encoding UTF-8 en consola de Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.services.gemini_service import GeminiService

def main():
    print("=" * 80)
    print("       MOTOR DE BUSQUEDA INTELIGENTE - FichaAI (Gemini AI)")
    print("=" * 80)
    print("Puedes escribir:")
    print(" 1. Solo el nombre del celular (ej: 'Tecno Spark 20 Pro', 'Samsung S24')")
    print(" 2. O pegar un texto con especificaciones tecnicas.")
    print(" (Escribe 'salir' para terminar)\n")

    while True:
        try:
            entrada = input("\n[>] Ingresa el modelo o texto del celular: ").strip()
            if not entrada:
                continue
            if entrada.lower() in ['salir', 'exit', 'q']:
                print("\nHasta luego!")
                break

            print(f"\n[...] Buscando datos oficiales completos y foto para: '{entrada}'...")
            
            resultado = GeminiService.extraer_ficha_desde_texto(entrada)
            
            print("\n" + "=" * 80)
            print("                 FICHA TECNICA COMPLETA GENERADA")
            print("=" * 80)
            print(f"  📱 Modelo:            {resultado.get('modelo')}")
            print(f"  🖥️  Pantalla:          {resultado.get('pantalla') or 'No especificada'}")
            print(f"  ⚡ Procesador:        {resultado.get('procesador') or 'No especificado'}")
            print(f"  🧠 Memoria RAM:       {resultado.get('ram') or 'No especificada'}")
            print(f"  💾 Almacenamiento:    {resultado.get('almacenamiento') or 'No especificado'}")
            print(f"  📸 Camara Principal:  {resultado.get('camara_principal') or 'No especificada'}")
            print(f"  🤳 Camara Frontal:    {resultado.get('camara_frontal') or 'No especificada'}")
            print(f"  🔋 Bateria y Carga:   {resultado.get('bateria') or 'No especificada'}")
            print(f"  ⚙️  Sist. Operativo:   {resultado.get('sistema_operativo') or 'No especificado'}")
            print(f"  📶 Conectividad:      {resultado.get('conectividad') or 'No especificada'}")
            print(f"  ✨ Extras:            {resultado.get('extras') or 'No especificados'}")
            print(f"  💰 Precio Oficial:    ${resultado.get('precio_oficial')} {resultado.get('moneda')}")
            print(f"  🖼️  Foto Oficial:      {resultado.get('url_imagen') or 'No disponible'}")
            print("=" * 80)
            print("\n[JSON Estructurado para Flutter / Base de Datos]:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
            print("-" * 80)

        except KeyboardInterrupt:
            print("\n\nSaliendo...")
            break
        except Exception as e:
            print(f"\n[ERROR] Ocurrio un problema: {e}")

if __name__ == '__main__':
    main()
