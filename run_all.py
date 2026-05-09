import signal
import subprocess
import sys
import time


def main():
    web_proc = subprocess.Popen([sys.executable, "run_web.py"])
    bot_proc = subprocess.Popen([sys.executable, "run_bot.py"])
    procs = [web_proc, bot_proc]

    def shutdown(*_args):
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("StickBot web + bot iniciados. Presiona CTRL+C para cerrar todo.")
    print("Si el bot falla, la web seguira funcionando para configuracion.")

    while True:
        web_exit = web_proc.poll()
        bot_exit = bot_proc.poll()
        if web_exit is not None:
            print(f"La web se cerro (code={web_exit}). Cerrando procesos.")
            shutdown()
        if bot_exit is not None:
            print(f"El bot se cerro (code={bot_exit}). La web sigue activa en http://localhost:8000")
            bot_proc = subprocess.Popen([sys.executable, "run_bot.py"])
            procs[1] = bot_proc
            print("Reintentando iniciar bot en segundo plano...")
        time.sleep(1)


if __name__ == "__main__":
    main()
