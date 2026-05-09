# Flujo OCR → MMR

```mermaid
flowchart LR
  User[Usuario adjunta imagen]
  DL[Bot descarga bytes]
  OCR[lector.analizar_captura]
  Val[Validar umbral puntos]
  MMR[persist_match guild_id]
  DB[(guild_player_stats)]
  User --> DL --> OCR --> Val --> MMR --> DB
```

- Parámetros OCR vienen de `guild_config` (márgenes, confianza, color).
- Sin imagen válida no hay MMR.
- Cada partida asocia `guild_id` en `partidas` y actualiza MMR solo en ese servidor.
