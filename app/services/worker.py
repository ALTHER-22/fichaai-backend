import queue
import threading
import time
from app import create_app

# Cola thread-safe para almacenar las tareas
task_queue = queue.Queue()

def worker_loop():
    # Creamos un contexto de aplicación para el worker para que pueda usar SQLAlchemy
    app = create_app()
    with app.app_context():
        while True:
            task = task_queue.get()
            if task is None:
                break
            
            task_type = task.get('type')
            task_data = task.get('data')
            
            try:
                print(f"[WORKER] Iniciando tarea asincrona: {task_type} con datos: {task_data}")
                if task_type == 'generar_reporte_pdf':
                    id_ficha = task_data.get('id_ficha')
                    
                    # Simular procesamiento pesado
                    time.sleep(3)
                    
                    from app.models.ficha_tecnica import FichaTecnica
                    ficha = FichaTecnica.query.get(id_ficha)
                    if ficha:
                        print(f"[WORKER] Reporte PDF generado exitosamente para la Ficha ID: {id_ficha} (Modelo: {ficha.modelo})")
                    else:
                        print(f"[WORKER] Error: Ficha ID {id_ficha} no encontrada para reporte.")
            except Exception as e:
                print(f"[WORKER] Error ejecutando la tarea {task_type}: {str(e)}")
            finally:
                task_queue.task_done()

# Hilo daemon para procesar tareas en background de forma asíncrona
worker_thread = threading.Thread(target=worker_loop, daemon=True)
worker_thread.start()

def enqueue_task(task_type, data):
    task = {'type': task_type, 'data': data}
    task_queue.put(task)
    print(f"[WORKER] Tarea '{task_type}' encolada exitosamente.")
