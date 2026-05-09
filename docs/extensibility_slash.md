# Extensión de comandos (slash) en Discord

- Los **nombres y descripciones** de slash commands se registran con `tree.sync()` al arrancar el bot; no se pueden crear comandos totalmente nuevos solo desde la base de datos sin desplegar código.
- **Opciones sin deploy:** editar textos vía `guild_message_templates`, políticas por comando en Manage, macros futuras que reutilicen un slash genérico.
- **Nuevo comando real:** añadir handler en [app/bot/client.py](app/bot/client.py), sincronizar, redeploy (p. ej. Railway).
